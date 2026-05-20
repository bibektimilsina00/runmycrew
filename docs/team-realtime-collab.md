  Architecture Decisions (need your sign-off)                                             
                                                                                            
  1. Workspace ownership model:                                                             
  Resources get workspace_id (full migration, 3-phase Alembic). user_id stays as created_by 
  audit field — not removed.                                                                
                                                                                            
  2. Workspace context in requests:                                                         
  X-Workspace-ID header (not URL prefix like /workspaces/{id}/workflows). Cleaner, doesn't  
  break existing routes/bookmarks. Same pattern as Slack, Linear, Notion.                   
                                                                                            
  3. Personal workspaces:                                                                   
  Every user gets one auto-created on signup. workspace_id is NEVER nullable. Simplest solo 
  users see "Personal Workspace" — but the data model is clean.                             
                                                                                            
  4. Roles:                                                                                 
  owner > admin > member > viewer                                                         
                                               
  5. Collab conflict strategy:                                                              
  Last-write-wins + conflict notification (not full CRDT/Yjs). Practical for workflow
  graphs. Version counter on each workflow.                                                 
           
  6. Real-time:                                                                             
  Redis pub/sub (same pattern as existing execution streaming). No in-memory state.       
                                                                                            
  ---                                                                                     
  Implementation Order (6 phases)              
                                                                                            
  Phase 0 — DB + Store foundations (parallel frontend/backend)
  Phase 1 — Workspace CRUD API                                                              
  Phase 2 — Migrate all resources to workspace_id scope
  Phase 3 — Workspace UI (selector, settings, invites, onboarding)                          
  Phase 4 — Real-time collaboration (WebSocket + cursors)                                   
  Phase 5 — Hardening (audit log, rate limits, edge cases)                                  
                                                                                            
  ---  