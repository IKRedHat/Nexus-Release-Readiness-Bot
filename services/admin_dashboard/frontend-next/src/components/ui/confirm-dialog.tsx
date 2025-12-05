'use client';

import * as React from 'react';
import { AlertTriangle, Trash2, Info } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './dialog';
import { Button } from './button';

export type ConfirmVariant = 'danger' | 'warning' | 'info';

export interface ConfirmDialogProps {
  /** Whether the dialog is open */
  open: boolean;
  /** Callback when dialog should close */
  onOpenChange: (open: boolean) => void;
  /** Dialog title */
  title: string;
  /** Dialog description/message */
  description: string;
  /** Text for confirm button */
  confirmText?: string;
  /** Text for cancel button */
  cancelText?: string;
  /** Callback when confirmed */
  onConfirm: () => void | Promise<void>;
  /** Callback when cancelled */
  onCancel?: () => void;
  /** Dialog variant - affects styling */
  variant?: ConfirmVariant;
  /** Whether confirm action is in progress */
  isLoading?: boolean;
  /** Additional content between description and buttons */
  children?: React.ReactNode;
}

/**
 * ConfirmDialog Component
 * 
 * A reusable confirmation dialog for destructive or important actions.
 * 
 * @example
 * // Delete confirmation
 * <ConfirmDialog
 *   open={showDelete}
 *   onOpenChange={setShowDelete}
 *   title="Delete Release"
 *   description="Are you sure you want to delete this release? This action cannot be undone."
 *   variant="danger"
 *   confirmText="Delete"
 *   onConfirm={handleDelete}
 * />
 * 
 * @example
 * // Warning confirmation
 * <ConfirmDialog
 *   open={showWarning}
 *   onOpenChange={setShowWarning}
 *   title="Publish Release"
 *   description="This will make the release available to all users."
 *   variant="warning"
 *   confirmText="Publish"
 *   onConfirm={handlePublish}
 * />
 */
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  variant = 'danger',
  isLoading = false,
  children,
}: ConfirmDialogProps) {
  const [isPending, setIsPending] = React.useState(false);

  const handleConfirm = async () => {
    setIsPending(true);
    try {
      await onConfirm();
      onOpenChange(false);
    } catch (error) {
      // Error handling should be done in onConfirm
      console.error('Confirm action failed:', error);
    } finally {
      setIsPending(false);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    }
    onOpenChange(false);
  };

  const icons = {
    danger: Trash2,
    warning: AlertTriangle,
    info: Info,
  };

  const iconColors = {
    danger: 'text-red-500 bg-red-500/10',
    warning: 'text-yellow-500 bg-yellow-500/10',
    info: 'text-blue-500 bg-blue-500/10',
  };

  const buttonVariants = {
    danger: 'destructive' as const,
    warning: 'default' as const,
    info: 'default' as const,
  };

  const Icon = icons[variant];
  const loading = isLoading || isPending;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className="flex items-start gap-4">
            <div className={`p-3 rounded-full ${iconColors[variant]}`}>
              <Icon className="w-6 h-6" />
            </div>
            <div className="flex-1">
              <DialogTitle className="text-lg">{title}</DialogTitle>
              <DialogDescription className="mt-2">
                {description}
              </DialogDescription>
            </div>
          </div>
        </DialogHeader>

        {children && <div className="py-4">{children}</div>}

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={handleCancel}
            disabled={loading}
          >
            {cancelText}
          </Button>
          <Button
            variant={buttonVariants[variant]}
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? 'Please wait...' : confirmText}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * Hook to manage confirm dialog state
 * 
 * @example
 * const { isOpen, openConfirm, closeConfirm, itemToDelete } = useConfirmDialog<Release>();
 * 
 * // In component
 * <Button onClick={() => openConfirm(release)}>Delete</Button>
 * <ConfirmDialog
 *   open={isOpen}
 *   onOpenChange={closeConfirm}
 *   title={`Delete ${itemToDelete?.name}`}
 *   onConfirm={() => handleDelete(itemToDelete)}
 * />
 */
export function useConfirmDialog<T = unknown>() {
  const [isOpen, setIsOpen] = React.useState(false);
  const [item, setItem] = React.useState<T | null>(null);

  const openConfirm = React.useCallback((itemToConfirm: T) => {
    setItem(itemToConfirm);
    setIsOpen(true);
  }, []);

  const closeConfirm = React.useCallback(() => {
    setIsOpen(false);
    // Delay clearing item to allow for exit animation
    setTimeout(() => setItem(null), 200);
  }, []);

  return {
    isOpen,
    item,
    openConfirm,
    closeConfirm,
    setIsOpen,
  };
}

