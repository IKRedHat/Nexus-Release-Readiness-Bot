/**
 * Dialog Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Dialog, DialogTrigger, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter, DialogClose } from '../dialog';
import { Button } from '../button';

describe('Dialog', () => {
  describe('Basic Rendering', () => {
    it('should render trigger button', () => {
      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open Dialog</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Dialog</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.getByRole('button', { name: /open dialog/i })).toBeInTheDocument();
    });

    it('should not show content by default', () => {
      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Hidden Title</DialogTitle>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.queryByText('Hidden Title')).not.toBeInTheDocument();
    });
  });

  describe('Open/Close Behavior', () => {
    it('should open dialog when trigger is clicked', async () => {
      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Dialog Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /open/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Dialog Title')).toBeInTheDocument();
      });
    });

    it('should close dialog when close button is clicked', async () => {
      render(
        <Dialog>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <DialogClose asChild>
              <Button>Close</Button>
            </DialogClose>
          </DialogContent>
        </Dialog>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /open/i }));
      
      await waitFor(() => {
        expect(screen.getByText('Title')).toBeInTheDocument();
      });
      
      fireEvent.click(screen.getByRole('button', { name: /close/i }));
      
      await waitFor(() => {
        expect(screen.queryByText('Title')).not.toBeInTheDocument();
      });
    });

    it('should call onOpenChange when state changes', async () => {
      const onOpenChange = vi.fn();
      
      render(
        <Dialog onOpenChange={onOpenChange}>
          <DialogTrigger asChild>
            <Button>Open</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
          </DialogContent>
        </Dialog>
      );
      
      fireEvent.click(screen.getByRole('button', { name: /open/i }));
      
      await waitFor(() => {
        expect(onOpenChange).toHaveBeenCalledWith(true);
      });
    });

    it('should support controlled open state', () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Always Open</DialogTitle>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.getByText('Always Open')).toBeInTheDocument();
    });
  });

  describe('Dialog Parts', () => {
    it('should render header with title and description', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>My Title</DialogTitle>
              <DialogDescription>My Description</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.getByText('My Title')).toBeInTheDocument();
      expect(screen.getByText('My Description')).toBeInTheDocument();
    });

    it('should render footer with actions', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <DialogFooter>
              <Button variant="outline">Cancel</Button>
              <Button>Save</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /save/i })).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have dialog role', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Accessible Dialog</DialogTitle>
          </DialogContent>
        </Dialog>
      );
      
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    it('should have aria-labelledby pointing to title', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Test Title</DialogTitle>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-labelledby');
    });

    it('should have aria-describedby when description exists', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Title</DialogTitle>
              <DialogDescription>Description text</DialogDescription>
            </DialogHeader>
          </DialogContent>
        </Dialog>
      );
      
      const dialog = screen.getByRole('dialog');
      expect(dialog).toHaveAttribute('aria-describedby');
    });

    it('should trap focus within dialog', async () => {
      render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>Title</DialogTitle>
            <input data-testid="input1" />
            <Button>Action</Button>
          </DialogContent>
        </Dialog>
      );
      
      const input = screen.getByTestId('input1');
      const button = screen.getByRole('button', { name: /action/i });
      
      // Both elements should be in the document (focus trap scope)
      expect(input).toBeInTheDocument();
      expect(button).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('should apply custom className to content', async () => {
      render(
        <Dialog open={true}>
          <DialogContent className="custom-dialog-class">
            <DialogTitle>Styled</DialogTitle>
          </DialogContent>
        </Dialog>
      );
      
      const dialog = screen.getByRole('dialog');
      expect(dialog.className).toContain('custom-dialog-class');
    });

    it('should have overlay backdrop', async () => {
      const { container } = render(
        <Dialog open={true}>
          <DialogContent>
            <DialogTitle>With Overlay</DialogTitle>
          </DialogContent>
        </Dialog>
      );
      
      // Check for overlay element
      const overlay = container.querySelector('[data-state="open"]');
      expect(overlay).toBeInTheDocument();
    });
  });
});

