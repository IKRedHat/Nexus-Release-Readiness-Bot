/**
 * Export Button Component
 * 
 * A dropdown button for exporting data in various formats.
 */

'use client';

import { useState } from 'react';
import { Download, FileText, FileJson, Printer, ChevronDown } from 'lucide-react';
import { Button } from './button';
import { exportData, ExportColumn, ExportOptions, ExportFormat } from '@/lib/export';
import { cn } from '@/lib/utils';

interface ExportButtonProps<T extends Record<string, unknown>> {
  data: T[];
  columns: ExportColumn<T>[];
  filename: string;
  title?: string;
  description?: string;
  className?: string;
  disabled?: boolean;
  formats?: ExportFormat[];
}

const formatConfig: Record<ExportFormat, { label: string; icon: React.ElementType }> = {
  csv: { label: 'Export CSV', icon: FileText },
  json: { label: 'Export JSON', icon: FileJson },
  print: { label: 'Print', icon: Printer },
};

export function ExportButton<T extends Record<string, unknown>>({
  data,
  columns,
  filename,
  title,
  description,
  className,
  disabled = false,
  formats = ['csv', 'json', 'print'],
}: ExportButtonProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async (format: ExportFormat) => {
    setIsExporting(true);
    setIsOpen(false);

    try {
      const options: ExportOptions = {
        filename,
        title,
        description,
        includeTimestamp: true,
      };

      exportData(format, data, columns, options);
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setIsExporting(false);
    }
  };

  // If only one format, show simple button
  if (formats.length === 1) {
    const format = formats[0];
    const config = formatConfig[format];
    const Icon = config.icon;

    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => handleExport(format)}
        disabled={disabled || isExporting || data.length === 0}
        className={className}
      >
        <Icon className="h-4 w-4 mr-2" />
        {config.label}
      </Button>
    );
  }

  // Multiple formats - show dropdown
  return (
    <div className={cn('relative', className)}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled || isExporting || data.length === 0}
        className="min-w-[120px]"
      >
        <Download className="h-4 w-4 mr-2" />
        {isExporting ? 'Exporting...' : 'Export'}
        <ChevronDown className={cn('h-4 w-4 ml-2 transition-transform', isOpen && 'rotate-180')} />
      </Button>

      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Dropdown */}
          <div className="absolute right-0 top-full mt-1 z-50 w-40 py-1 bg-popover border border-border rounded-md shadow-lg">
            {formats.map((format) => {
              const config = formatConfig[format];
              const Icon = config.icon;

              return (
                <button
                  key={format}
                  onClick={() => handleExport(format)}
                  className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent transition-colors"
                >
                  <Icon className="h-4 w-4" />
                  <span>{config.label}</span>
                </button>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

export default ExportButton;

