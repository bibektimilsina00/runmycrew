// shadcn/ui primitives — Fuse-styled
export { Button, type ButtonProps } from './button'
export { buttonVariants } from './button.variants'
export { Input, type InputProps } from './input'
export { Textarea, type TextareaProps } from './textarea'
export { Label } from './label'
export { Badge, type BadgeProps } from './badge'
export { badgeVariants } from './badge.variants'
export { Checkbox } from './checkbox'
export { Switch } from './switch'
export { Separator } from './separator'
export { Skeleton, SkeletonText, SkeletonCard } from './skeleton'
export { Progress } from './progress'

// Layout / containers
export {
  Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter,
} from './card'
export { ScrollArea, ScrollBar } from './scroll-area'

// Overlays
export {
  Modal,
  DialogRoot, DialogTrigger, DialogPortal, DialogClose,
  DialogOverlay, DialogContent, DialogHeader, DialogFooter,
  DialogBody, DialogTitle, DialogDescription,
} from './dialog'
export {
  Popover, PopoverRoot, PopoverTrigger, PopoverAnchor, PopoverContent,
} from './popover'
export {
  Tooltip, TooltipProvider, TooltipRoot, TooltipTrigger, TooltipContent,
} from './tooltip'

// Menus
export {
  DropdownMenuRoot, DropdownMenuTrigger, DropdownMenuGroup, DropdownMenuPortal,
  DropdownMenuSub, DropdownMenuRadioGroup, DropdownMenuSubTrigger,
  DropdownMenuSubContent, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuCheckboxItem, DropdownMenuSeparator, DropdownMenuLabel,
  // Legacy aliases
  Dropdown, DropdownTrigger, DropdownContent, DropdownItem, DropdownSeparator,
} from './dropdown-menu'

// Navigation
export { Tabs, TabsList, TabsTrigger, TabsContent } from './tabs'

// Forms
export {
  Select, SelectRoot, SelectGroup, SelectValue, SelectTrigger, SelectContent,
  SelectLabel, SelectItem, SelectSeparator, SelectScrollUpButton,
  SelectScrollDownButton, type SelectOption,
} from './select'

// Table
export {
  Table, TableHeader, TableBody, TableFooter, TableHead, TableRow,
  TableCell, TableCaption, TableTh, TableTd,
} from './table'

// Utility / new
export {
  SheetRoot, SheetContent, SheetHeader, SheetFooter, SheetTitle,
  SheetDescription, SheetTrigger, SheetClose, SheetOverlay, SheetPortal,
} from './sheet'
export {
  Command, CommandDialog, CommandInput, CommandList, CommandEmpty,
  CommandGroup, CommandItem, CommandShortcut, CommandSeparator,
} from './command'
export { Toaster } from './sonner'
