/**
 * Export Utilities
 * 
 * Provides functionality to export data in various formats:
 * - CSV
 * - JSON
 * - Print-ready HTML
 */

import { saveAs } from 'file-saver';
import { format } from 'date-fns';

// =============================================================================
// Types
// =============================================================================

export interface ExportColumn<T> {
  key: keyof T | string;
  header: string;
  formatter?: (value: unknown, row: T) => string;
}

export interface ExportOptions {
  filename: string;
  title?: string;
  description?: string;
  includeTimestamp?: boolean;
}

// =============================================================================
// CSV Export
// =============================================================================

/**
 * Export data to CSV format
 */
export function exportToCSV<T extends Record<string, unknown>>(
  data: T[],
  columns: ExportColumn<T>[],
  options: ExportOptions
): void {
  if (!data.length) {
    console.warn('No data to export');
    return;
  }

  // Build header row
  const headers = columns.map((col) => escapeCSVValue(col.header));
  
  // Build data rows
  const rows = data.map((row) =>
    columns.map((col) => {
      const value = getNestedValue(row, col.key as string);
      const formattedValue = col.formatter
        ? col.formatter(value, row)
        : formatValue(value);
      return escapeCSVValue(formattedValue);
    })
  );

  // Combine into CSV string
  const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');

  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
  const filename = buildFilename(options, 'csv');
  saveAs(blob, filename);
}

/**
 * Escape a value for CSV format
 */
function escapeCSVValue(value: string): string {
  if (value === null || value === undefined) {
    return '';
  }
  
  const stringValue = String(value);
  
  // If value contains comma, newline, or double quote, wrap in quotes
  if (stringValue.includes(',') || stringValue.includes('\n') || stringValue.includes('"')) {
    return `"${stringValue.replace(/"/g, '""')}"`;
  }
  
  return stringValue;
}

// =============================================================================
// JSON Export
// =============================================================================

/**
 * Export data to JSON format
 */
export function exportToJSON<T>(
  data: T[],
  options: ExportOptions
): void {
  if (!data.length) {
    console.warn('No data to export');
    return;
  }

  const exportData = {
    exportedAt: new Date().toISOString(),
    title: options.title || options.filename,
    description: options.description,
    count: data.length,
    data,
  };

  const jsonContent = JSON.stringify(exportData, null, 2);
  const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8' });
  const filename = buildFilename(options, 'json');
  saveAs(blob, filename);
}

// =============================================================================
// Print Export
// =============================================================================

/**
 * Export data for printing (opens print dialog)
 */
export function exportToPrint<T extends Record<string, unknown>>(
  data: T[],
  columns: ExportColumn<T>[],
  options: ExportOptions
): void {
  if (!data.length) {
    console.warn('No data to export');
    return;
  }

  // Build HTML table
  const headerCells = columns
    .map((col) => `<th style="padding: 8px; border: 1px solid #ddd; text-align: left;">${col.header}</th>`)
    .join('');

  const bodyRows = data
    .map((row) => {
      const cells = columns
        .map((col) => {
          const value = getNestedValue(row, col.key as string);
          const formattedValue = col.formatter
            ? col.formatter(value, row)
            : formatValue(value);
          return `<td style="padding: 8px; border: 1px solid #ddd;">${formattedValue}</td>`;
        })
        .join('');
      return `<tr>${cells}</tr>`;
    })
    .join('');

  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <title>${options.title || options.filename}</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            padding: 20px;
            color: #333;
          }
          h1 {
            margin-bottom: 10px;
          }
          .meta {
            color: #666;
            margin-bottom: 20px;
          }
          table {
            width: 100%;
            border-collapse: collapse;
          }
          th {
            background-color: #f5f5f5;
          }
          tr:nth-child(even) {
            background-color: #f9f9f9;
          }
          @media print {
            body { padding: 0; }
          }
        </style>
      </head>
      <body>
        <h1>${options.title || options.filename}</h1>
        <div class="meta">
          ${options.description ? `<p>${options.description}</p>` : ''}
          <p>Exported: ${format(new Date(), 'PPpp')}</p>
          <p>Total Records: ${data.length}</p>
        </div>
        <table>
          <thead>
            <tr>${headerCells}</tr>
          </thead>
          <tbody>
            ${bodyRows}
          </tbody>
        </table>
      </body>
    </html>
  `;

  // Open print window
  const printWindow = window.open('', '_blank');
  if (printWindow) {
    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.print();
  }
}

// =============================================================================
// Helpers
// =============================================================================

/**
 * Build filename with optional timestamp
 */
function buildFilename(options: ExportOptions, extension: string): string {
  let filename = options.filename.replace(/[^a-zA-Z0-9-_]/g, '_');
  
  if (options.includeTimestamp !== false) {
    const timestamp = format(new Date(), 'yyyy-MM-dd_HHmmss');
    filename = `${filename}_${timestamp}`;
  }
  
  return `${filename}.${extension}`;
}

/**
 * Get a nested value from an object using dot notation
 */
function getNestedValue(obj: Record<string, unknown>, path: string): unknown {
  return path.split('.').reduce((acc: unknown, part: string) => {
    if (acc && typeof acc === 'object' && part in acc) {
      return (acc as Record<string, unknown>)[part];
    }
    return undefined;
  }, obj);
}

/**
 * Format a value for display
 */
function formatValue(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }
  
  if (value instanceof Date) {
    return format(value, 'PPpp');
  }
  
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  
  if (Array.isArray(value)) {
    return value.join(', ');
  }
  
  if (typeof value === 'object') {
    return JSON.stringify(value);
  }
  
  return String(value);
}

// =============================================================================
// Export All Formats
// =============================================================================

export type ExportFormat = 'csv' | 'json' | 'print';

/**
 * Export data in the specified format
 */
export function exportData<T extends Record<string, unknown>>(
  format: ExportFormat,
  data: T[],
  columns: ExportColumn<T>[],
  options: ExportOptions
): void {
  switch (format) {
    case 'csv':
      exportToCSV(data, columns, options);
      break;
    case 'json':
      exportToJSON(data, options);
      break;
    case 'print':
      exportToPrint(data, columns, options);
      break;
    default:
      console.error(`Unsupported export format: ${format}`);
  }
}

export default exportData;

