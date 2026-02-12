import React from 'react';
import { Calendar } from 'lucide-react';

interface DateRangePickerProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  onClear: () => void;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  onClear
}) => {
  return (
    <div className="flex items-center gap-2 bg-white p-2 rounded-lg border border-gray-200 shadow-sm">
      <Calendar size={16} className="text-gray-500" />
      <div className="flex items-center gap-2 text-sm">
        <input
          type="date"
          value={startDate}
          onChange={(e) => onStartDateChange(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-gray-700 outline-none focus:border-blue-500"
        />
        <span className="text-gray-400">→</span>
        <input
          type="date"
          value={endDate}
          onChange={(e) => onEndDateChange(e.target.value)}
          className="border border-gray-300 rounded px-2 py-1 text-gray-700 outline-none focus:border-blue-500"
        />
      </div>
      {(startDate || endDate) && (
        <button
          onClick={onClear}
          className="ml-2 text-xs text-red-500 hover:text-red-700 font-medium"
        >
          Limpiar
        </button>
      )}
    </div>
  );
};
