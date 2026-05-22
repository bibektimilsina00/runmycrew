import asyncio
import json
import uuid
from contextlib import suppress
from datetime import UTC, datetime

from fastapi import WebSocket
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.websockets import WebSocketState

from apps.api.app.core.logger import get_logger
from apps.api.app.core.redis import get_redis
from apps.api.app.core.security import get_current_user_from_token
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.repositories.workflow_repository import WorkflowRepository
from apps.api.app.schemas.websocket import (
    CollaborationClientEvent,
    CollaborationServerEvent,
    CollaborationSession,
)
from apps.api.app.services.workspace_service import WorkspaceService

logger = get_logger(__name__)

COLORS = ["#2563eb", "#059669", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#be123c"]


class CollaborationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def authenticate(
        self,
        token: str,
        workspace_id: uuid.UUID,
        workflow_id: uuid.UUID,
    ) -> tuple[User, Workspace, CollaborationSession]:
        user = await get_current_user_from_token(token)
        if user is None:
            raise PermissionError("Invalid token")
        workspace = await WorkspaceService(self.db).resolve_workspace(user, workspace_id)
        workflow = await WorkflowRepository(self.db).get_by_id_and_workspace(workflow_id, workspace.id)
        if workflow is None:
            raise PermissionError("Workflow not found")
        session = CollaborationSession(
            session_id=str(uuid.uuid4()),
            user_id=str(user.id),
            user_name=self.display_name(user),
            avatar_url=user.avatar_url,
            color=COLORS[int(user.id.hex[:8], 16) % len(COLORS)],
            connected_at=datetime.now(UTC).isoformat(),
        )
        return user, workspace, session

    def display_name(self, user: User) -> str:
        source = (user.full_name or "").strip() or user.email.split("@", 1)[0]
        first_name = source.split(maxsplit=1)[0].strip()
        return first_name or "User"

    def channel(self, workflow_id: uuid.UUID) -> str:
        return f"collab:workflow:{workflow_id}"

    async def presence_key(self, workflow_id: uuid.UUID) -> str:
        return f"collab:workflow:{workflow_id}:presence"

    async def add_presence(self, workflow_id: uuid.UUID, session: CollaborationSession) -> None:
        redis = await get_redis()
        await redis.hset(await self.presence_key(workflow_id), session.session_id, session.model_dump_json())
        await redis.expire(await self.presence_key(workflow_id), 300)  # 5-min safety net — primary cleanup via timeout

    async def remove_presence(self, workflow_id: uuid.UUID, session_id: str) -> None:
        redis = await get_redis()
        await redis.hdel(await self.presence_key(workflow_id), session_id)

    async def list_presence(self, workflow_id: uuid.UUID) -> list[CollaborationSession]:
        redis = await get_redis()
        raw = await redis.hvals(await self.presence_key(workflow_id))
        sessions: list[CollaborationSession] = []
        for item in raw:
            try:
                value = item.decode() if isinstance(item, bytes) else item
                sessions.append(CollaborationSession.model_validate_json(value))
            except ValidationError:
                logger.warning("Ignoring invalid collaboration presence payload")
        return sessions

    async def publish(
        self,
        workflow_id: uuid.UUID,
        event: CollaborationServerEvent,
        exclude_session_id: str | None = None,
    ) -> None:
        redis = await get_redis()
        payload = event.model_dump(mode="json")
        if exclude_session_id:
            payload["_exclude_session_id"] = exclude_session_id
        await redis.publish(self.channel(workflow_id), json.dumps(payload))

    async def forward_pubsub(
        self, websocket: WebSocket, workflow_id: uuid.UUID, session_id: str
    ) -> None:
        redis = await get_redis()
        pubsub = redis.pubsub()
        await pubsub.subscribe(self.channel(workflow_id))
        try:
            async for message in pubsub.listen():
                if message["type"] != "message":
                    continue
                data = json.loads(message["data"])
                if data.pop("_exclude_session_id", None) == session_id:
                    continue
                await websocket.send_json(data)
        finally:
            await pubsub.unsubscribe(self.channel(workflow_id))

    async def receive_and_publish(
        self,
        websocket: WebSocket,
        workflow_id: uuid.UUID,
        session: CollaborationSession,
    ) -> None:
        # Client sends heartbeat every 30s. If we receive nothing for 60s the
        # connection is dead (tab closed, network drop) — raise TimeoutError so
        # run_socket's finally block removes presence and broadcasts presence.left.
        RECEIVE_TIMEOUT = 60.0

        while True:
            try:
                raw = await asyncio.wait_for(websocket.receive_text(), timeout=RECEIVE_TIMEOUT)
            except TimeoutError:
                logger.info(f"[collab] session {session.session_id} timed out — removing presence")
                return  # causes run_socket finally to clean up

            try:
                event = CollaborationClientEvent.model_validate_json(raw)
            except ValidationError as exc:
                await websocket.send_json(
                    CollaborationServerEvent(
                        type="error",
                        payload={"message": "Invalid collaboration event", "details": exc.errors()},
                    ).model_dump(mode="json")
                )
                continue
            # Heartbeat: no broadcast, just keeps the loop alive
            if event.type == "heartbeat":
                continue

            await self.publish(
                workflow_id,
                CollaborationServerEvent(
                    type=event.type,
                    session=session,
                    payload=event.payload,
                    patch_id=event.patch_id,
                ),
                exclude_session_id=session.session_id,
            )

    async def run_socket(
        self,
        websocket: WebSocket,
        workflow_id: uuid.UUID,
        token: str,
        workspace_id: uuid.UUID,
    ) -> None:
        try:
            _, _, session = await self.authenticate(token, workspace_id, workflow_id)
        except PermissionError:
            await websocket.close(code=4001)
            return

        await websocket.accept()
        await self.add_presence(workflow_id, session)
        await websocket.send_json(
            CollaborationServerEvent(type="session.ready", session=session).model_dump(mode="json")
        )
        await websocket.send_json(
            CollaborationServerEvent(
                type="presence.snapshot",
                sessions=await self.list_presence(workflow_id),
            ).model_dump(mode="json")
        )
        await self.publish(
            workflow_id,
            CollaborationServerEvent(type="presence.joined", session=session),
            exclude_session_id=session.session_id,
        )

        listen_task = asyncio.create_task(self.forward_pubsub(websocket, workflow_id, session.session_id))
        receive_task = asyncio.create_task(self.receive_and_publish(websocket, workflow_id, session))
        try:
            done, pending = await asyncio.wait(
                {listen_task, receive_task},
                return_when=asyncio.FIRST_COMPLETED,
            )
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
        finally:
            await self.remove_presence(workflow_id, session.session_id)
            await self.publish(
                workflow_id,
                CollaborationServerEvent(type="presence.left", session=session),
                exclude_session_id=session.session_id,
            )
            if websocket.client_state != WebSocketState.DISCONNECTED:
                with suppress(Exception):
                    await websocket.close(code=1000)
