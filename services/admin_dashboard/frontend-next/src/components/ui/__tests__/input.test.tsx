/**
 * Input Component Tests
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Input } from '../input';

describe('Input', () => {
  describe('Rendering', () => {
    it('should render input element', () => {
      render(<Input placeholder="Enter text" />);
      expect(screen.getByPlaceholderText('Enter text')).toBeInTheDocument();
    });

    it('should render with type text by default', () => {
      render(<Input data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'text');
    });

    it('should forward ref', () => {
      const ref = vi.fn();
      render(<Input ref={ref} />);
      expect(ref).toHaveBeenCalled();
    });
  });

  describe('Input Types', () => {
    it('should render email input', () => {
      render(<Input type="email" data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'email');
    });

    it('should render password input', () => {
      render(<Input type="password" data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'password');
    });

    it('should render number input', () => {
      render(<Input type="number" data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'number');
    });

    it('should render search input', () => {
      render(<Input type="search" data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'search');
    });

    it('should render tel input', () => {
      render(<Input type="tel" data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'tel');
    });

    it('should render url input', () => {
      render(<Input type="url" data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'url');
    });
  });

  describe('Value Handling', () => {
    it('should display value', () => {
      render(<Input value="test value" readOnly />);
      expect(screen.getByDisplayValue('test value')).toBeInTheDocument();
    });

    it('should handle onChange', () => {
      const onChange = vi.fn();
      render(<Input onChange={onChange} />);
      
      fireEvent.change(screen.getByRole('textbox'), { target: { value: 'new value' } });
      expect(onChange).toHaveBeenCalled();
    });

    it('should update value on change', () => {
      const { rerender } = render(<Input value="" readOnly />);
      expect(screen.getByRole('textbox')).toHaveValue('');
      
      rerender(<Input value="updated" readOnly />);
      expect(screen.getByRole('textbox')).toHaveValue('updated');
    });
  });

  describe('States', () => {
    it('should be disabled when disabled prop is true', () => {
      render(<Input disabled />);
      expect(screen.getByRole('textbox')).toBeDisabled();
    });

    it('should be readonly when readOnly prop is true', () => {
      render(<Input readOnly />);
      expect(screen.getByRole('textbox')).toHaveAttribute('readonly');
    });

    it('should be required when required prop is true', () => {
      render(<Input required />);
      expect(screen.getByRole('textbox')).toBeRequired();
    });
  });

  describe('Styling', () => {
    it('should have base input styles', () => {
      render(<Input data-testid="input" />);
      const input = screen.getByTestId('input');
      expect(input.className).toContain('rounded-md');
      expect(input.className).toContain('border');
    });

    it('should have height class', () => {
      render(<Input data-testid="input" />);
      expect(screen.getByTestId('input').className).toContain('h-10');
    });

    it('should have full width', () => {
      render(<Input data-testid="input" />);
      expect(screen.getByTestId('input').className).toContain('w-full');
    });

    it('should apply custom className', () => {
      render(<Input className="custom-input" data-testid="input" />);
      expect(screen.getByTestId('input').className).toContain('custom-input');
    });

    it('should have focus ring styles', () => {
      render(<Input data-testid="input" />);
      const input = screen.getByTestId('input');
      expect(input.className).toContain('focus-visible:ring-2');
    });

    it('should have disabled styles', () => {
      render(<Input disabled data-testid="input" />);
      const input = screen.getByTestId('input');
      expect(input.className).toContain('disabled:opacity-50');
      expect(input.className).toContain('disabled:cursor-not-allowed');
    });
  });

  describe('Placeholder', () => {
    it('should display placeholder', () => {
      render(<Input placeholder="Enter your email" />);
      expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    });

    it('should have placeholder styling', () => {
      render(<Input placeholder="Placeholder" data-testid="input" />);
      expect(screen.getByTestId('input').className).toContain('placeholder:text-muted-foreground');
    });
  });

  describe('Accessibility', () => {
    it('should have textbox role for text input', () => {
      render(<Input type="text" />);
      expect(screen.getByRole('textbox')).toBeInTheDocument();
    });

    it('should support aria-label', () => {
      render(<Input aria-label="Email address" />);
      expect(screen.getByRole('textbox', { name: 'Email address' })).toBeInTheDocument();
    });

    it('should support aria-describedby', () => {
      render(
        <>
          <Input aria-describedby="help-text" />
          <span id="help-text">Enter your email</span>
        </>
      );
      expect(screen.getByRole('textbox')).toHaveAttribute('aria-describedby', 'help-text');
    });
  });

  describe('File Input', () => {
    it('should render file input', () => {
      render(<Input type="file" data-testid="input" />);
      expect(screen.getByTestId('input')).toHaveAttribute('type', 'file');
    });

    it('should have file input styles', () => {
      render(<Input type="file" data-testid="input" />);
      const input = screen.getByTestId('input');
      expect(input.className).toContain('file:border-0');
      expect(input.className).toContain('file:bg-transparent');
    });
  });
});

