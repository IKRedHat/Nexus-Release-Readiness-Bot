/**
 * Advanced Data Table Component
 * 
 * A feature-rich data table built with @tanstack/react-table.
 * Features:
 * - Sorting
 * - Filtering
 * - Pagination
 * - Row selection
 * - Column visibility
 * - Export support
 */

'use client';

import { useState, useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  ColumnFiltersState,
  VisibilityState,
  RowSelectionState,
  FilterFn,
} from '@tanstack/react-table';
import {
  ChevronDown,
  ChevronUp,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Search,
  Settings2,
  Check,
} from 'lucide-react';
import { Button } from './button';
import { Input } from './input';
import { ExportButton } from './export-button';
import { cn } from '@/lib/utils';
import type { ExportColumn } from '@/lib/export';

// =============================================================================
// Types
// =============================================================================

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  searchPlaceholder?: string;
  searchColumn?: string;
  enableRowSelection?: boolean;
  enableColumnVisibility?: boolean;
  enableExport?: boolean;
  exportFilename?: string;
  pageSize?: number;
  className?: string;
  onRowClick?: (row: TData) => void;
}

// =============================================================================
// Component
// =============================================================================

export function DataTable<TData extends Record<string, unknown>, TValue>({
  columns,
  data,
  searchPlaceholder = 'Search...',
  searchColumn,
  enableRowSelection = false,
  enableColumnVisibility = false,
  enableExport = false,
  exportFilename = 'data-export',
  pageSize = 10,
  className,
  onRowClick,
}: DataTableProps<TData, TValue>) {
  // State
  const [sorting, setSorting] = useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState('');
  const [showColumnSelector, setShowColumnSelector] = useState(false);

  // Global filter function
  const fuzzyFilter: FilterFn<TData> = (row, columnId, value) => {
    const itemValue = row.getValue(columnId);
    if (itemValue == null) return false;
    
    const searchValue = String(value).toLowerCase();
    const itemString = String(itemValue).toLowerCase();
    
    return itemString.includes(searchValue);
  };

  // Table instance
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    onRowSelectionChange: setRowSelection,
    onGlobalFilterChange: setGlobalFilter,
    globalFilterFn: fuzzyFilter,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
      rowSelection,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize,
      },
    },
  });

  // Export columns configuration
  const exportColumns: ExportColumn<TData>[] = useMemo(() => {
    return columns
      .filter((col) => 'accessorKey' in col && col.accessorKey)
      .map((col) => ({
        key: (col as { accessorKey: string }).accessorKey,
        header: typeof col.header === 'string' ? col.header : String((col as { accessorKey: string }).accessorKey),
      }));
  }, [columns]);

  return (
    <div className={cn('space-y-4', className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-4">
        {/* Search */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder={searchPlaceholder}
            value={searchColumn 
              ? (table.getColumn(searchColumn)?.getFilterValue() as string) ?? ''
              : globalFilter
            }
            onChange={(e) => {
              if (searchColumn) {
                table.getColumn(searchColumn)?.setFilterValue(e.target.value);
              } else {
                setGlobalFilter(e.target.value);
              }
            }}
            className="pl-9"
          />
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Column Visibility */}
          {enableColumnVisibility && (
            <div className="relative">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowColumnSelector(!showColumnSelector)}
              >
                <Settings2 className="h-4 w-4 mr-2" />
                Columns
                <ChevronDown className={cn('h-4 w-4 ml-2 transition-transform', showColumnSelector && 'rotate-180')} />
              </Button>

              {showColumnSelector && (
                <>
                  <div
                    className="fixed inset-0 z-40"
                    onClick={() => setShowColumnSelector(false)}
                  />
                  <div className="absolute right-0 top-full mt-1 z-50 w-48 py-1 bg-popover border border-border rounded-md shadow-lg">
                    {table.getAllColumns()
                      .filter((column) => column.getCanHide())
                      .map((column) => (
                        <button
                          key={column.id}
                          onClick={() => column.toggleVisibility(!column.getIsVisible())}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent transition-colors"
                        >
                          <div className={cn(
                            'h-4 w-4 border rounded flex items-center justify-center',
                            column.getIsVisible() ? 'bg-primary border-primary' : 'border-input'
                          )}>
                            {column.getIsVisible() && <Check className="h-3 w-3 text-primary-foreground" />}
                          </div>
                          <span className="capitalize">{column.id.replace(/_/g, ' ')}</span>
                        </button>
                      ))}
                  </div>
                </>
              )}
            </div>
          )}

          {/* Export */}
          {enableExport && (
            <ExportButton
              data={data}
              columns={exportColumns}
              filename={exportFilename}
            />
          )}
        </div>
      </div>

      {/* Table */}
      <div className="border border-border rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-sm font-medium text-muted-foreground"
                      style={{ width: header.getSize() }}
                    >
                      {header.isPlaceholder ? null : (
                        <div
                          className={cn(
                            'flex items-center gap-2',
                            header.column.getCanSort() && 'cursor-pointer select-none hover:text-foreground'
                          )}
                          onClick={header.column.getToggleSortingHandler()}
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          {header.column.getCanSort() && (
                            <span className="text-muted-foreground">
                              {header.column.getIsSorted() === 'asc' ? (
                                <ChevronUp className="h-4 w-4" />
                              ) : header.column.getIsSorted() === 'desc' ? (
                                <ChevronDown className="h-4 w-4" />
                              ) : (
                                <ChevronsUpDown className="h-4 w-4 opacity-50" />
                              )}
                            </span>
                          )}
                        </div>
                      )}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-border">
              {table.getRowModel().rows.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length}
                    className="px-4 py-8 text-center text-muted-foreground"
                  >
                    No results found.
                  </td>
                </tr>
              ) : (
                table.getRowModel().rows.map((row) => (
                  <tr
                    key={row.id}
                    className={cn(
                      'hover:bg-muted/50 transition-colors',
                      row.getIsSelected() && 'bg-accent',
                      onRowClick && 'cursor-pointer'
                    )}
                    onClick={() => onRowClick?.(row.original)}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-3 text-sm">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {enableRowSelection && (
            <span>
              {table.getFilteredSelectedRowModel().rows.length} of{' '}
              {table.getFilteredRowModel().rows.length} row(s) selected.
            </span>
          )}
          {!enableRowSelection && (
            <span>
              Showing {table.getState().pagination.pageIndex * table.getState().pagination.pageSize + 1} to{' '}
              {Math.min(
                (table.getState().pagination.pageIndex + 1) * table.getState().pagination.pageSize,
                table.getFilteredRowModel().rows.length
              )}{' '}
              of {table.getFilteredRowModel().rows.length} results
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => table.setPageIndex(0)}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronsLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          <span className="text-sm text-muted-foreground px-2">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>

          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            className="h-8 w-8"
            onClick={() => table.setPageIndex(table.getPageCount() - 1)}
            disabled={!table.getCanNextPage()}
          >
            <ChevronsRight className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}

export default DataTable;

