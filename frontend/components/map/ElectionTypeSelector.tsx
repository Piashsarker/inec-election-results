'use client';

import * as Select from '@radix-ui/react-select';
import { ElectionTypeOption } from '@/types';

interface ElectionTypeSelectorProps {
  electionTypes: ElectionTypeOption[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loading?: boolean;
}

export function ElectionTypeSelector({
  electionTypes,
  selectedId,
  onSelect,
  loading,
}: ElectionTypeSelectorProps) {
  if (loading) {
    return (
      <div className="inline-flex items-center gap-2 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800">
        <svg
          className="animate-spin h-4 w-4 text-gray-400"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        Loading election types...
      </div>
    );
  }

  return (
    <Select.Root value={selectedId ?? undefined} onValueChange={onSelect}>
      <Select.Trigger
        className="inline-flex items-center justify-between gap-2 border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-2 text-sm text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 hover:border-gray-400 dark:hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1 min-w-[200px]"
        aria-label="Select election type"
      >
        <Select.Value placeholder="Select election type..." />
        <Select.Icon>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            className="text-gray-500"
          >
            <path d="M3 4.5l3 3 3-3" />
          </svg>
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          className="overflow-hidden bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-50"
          position="popper"
          sideOffset={4}
        >
          <Select.Viewport className="p-1">
            {electionTypes.map((electionType) => (
              <Select.Item
                key={electionType.id}
                value={electionType.id}
                className="relative flex items-center px-3 py-2 text-sm text-gray-900 dark:text-gray-100 rounded-md cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 focus:bg-gray-100 dark:focus:bg-gray-700 outline-none data-[highlighted]:bg-gray-100 dark:data-[highlighted]:bg-gray-700"
              >
                <Select.ItemText>{electionType.name}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}

export default ElectionTypeSelector;
