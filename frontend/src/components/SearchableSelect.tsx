import React, { useState, useRef, useEffect } from "react";
import { Search, ChevronDown, Check, X } from "lucide-react";

export interface SelectOption {
  value: string;
  label: string;
  category?: string;
  sublabel?: string;
  badge?: string;
}

export interface SearchableSelectProps {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  icon?: React.ReactNode;
  label?: string;
  disabled?: boolean;
}

export const SearchableSelect: React.FC<SearchableSelectProps> = ({
  options,
  value,
  onChange,
  placeholder = "Select an option...",
  searchPlaceholder = "Search...",
  icon,
  label,
  disabled = false,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Close when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  const selectedOption = options.find((o) => o.value === value);

  // Filter options based on search query
  const filteredOptions = options.filter((o) => {
    const q = searchTerm.toLowerCase();
    return (
      o.label.toLowerCase().includes(q) ||
      (o.sublabel && o.sublabel.toLowerCase().includes(q)) ||
      (o.category && o.category.toLowerCase().includes(q))
    );
  });

  // Group by category if present
  const categories = Array.from(
    new Set(filteredOptions.map((o) => o.category || "General"))
  );

  const handleSelect = (val: string) => {
    onChange(val);
    setIsOpen(false);
    setSearchTerm("");
  };

  return (
    <div className="relative w-full" ref={containerRef}>
      {label && (
        <label className="block text-xs font-semibold text-slate-700 mb-1">
          {label}
        </label>
      )}

      {/* Trigger Button */}
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full bg-slate-50 border rounded-xl px-3.5 py-2.5 text-sm text-left font-medium transition-all flex items-center justify-between gap-2 shadow-sm ${
          isOpen
            ? "border-emerald-500 ring-2 ring-emerald-500/20 bg-white"
            : "border-slate-300 hover:border-slate-400"
        } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
      >
        <div className="flex items-center gap-2.5 truncate">
          {icon && <span className="text-emerald-700 flex-shrink-0">{icon}</span>}
          {selectedOption ? (
            <div className="truncate">
              <span className="text-slate-900 font-semibold">{selectedOption.label}</span>
              {selectedOption.sublabel && (
                <span className="text-slate-600 text-xs ml-2 truncate">
                  ({selectedOption.sublabel})
                </span>
              )}
            </div>
          ) : (
            <span className="text-slate-600">{placeholder}</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {selectedOption?.badge && (
            <span className="text-[10px] uppercase font-bold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
              {selectedOption.badge}
            </span>
          )}
          <ChevronDown
            className={`w-4 h-4 text-slate-500 transition-transform duration-150 ${
              isOpen ? "rotate-180" : ""
            }`}
          />
        </div>
      </button>

      {/* Floating Dropdown */}
      {isOpen && (
        <div className="absolute left-0 right-0 top-full mt-1.5 bg-white rounded-xl shadow-xl border border-slate-200 z-50 overflow-hidden max-h-80 flex flex-col animate-in fade-in zoom-in-95 duration-100">
          {/* Search Box Header */}
          <div className="p-2 border-b border-slate-100 bg-slate-50/80 sticky top-0 flex items-center gap-2">
            <Search className="w-4 h-4 text-slate-500 ml-1 flex-shrink-0" />
            <input
              ref={inputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder={searchPlaceholder}
              className="w-full bg-transparent text-xs text-slate-800 placeholder-slate-600 focus:outline-none"
            />
            {searchTerm && (
              <button
                type="button"
                onClick={() => setSearchTerm("")}
                className="text-slate-500 hover:text-slate-700 p-0.5"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>

          {/* Options List */}
          <div className="overflow-y-auto flex-1 p-1 divide-y divide-slate-100">
            {filteredOptions.length === 0 ? (
              <div className="py-6 text-center text-xs text-slate-600">
                No matching results found for "{searchTerm}"
              </div>
            ) : (
              categories.map((cat) => {
                const groupItems = filteredOptions.filter(
                  (o) => (o.category || "General") === cat
                );
                if (groupItems.length === 0) return null;

                return (
                  <div key={cat} className="py-1">
                    {cat !== "General" && (
                      <div className="px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-900 bg-emerald-50/70 rounded-md my-0.5">
                        {cat}
                      </div>
                    )}
                    {groupItems.map((item) => {
                      const isSelected = item.value === value;
                      return (
                        <button
                          key={item.value}
                          type="button"
                          onClick={() => handleSelect(item.value)}
                          className={`w-full text-left px-2.5 py-2 rounded-lg text-xs flex items-center justify-between transition-colors ${
                            isSelected
                              ? "bg-emerald-600 text-white font-semibold"
                              : "hover:bg-slate-100 text-slate-800"
                          }`}
                        >
                          <div className="truncate pr-2">
                            <span className="font-medium">{item.label}</span>
                            {item.sublabel && (
                              <span
                                className={`text-[11px] ml-1.5 ${
                                  isSelected ? "text-emerald-100" : "text-slate-600"
                                }`}
                              >
                                • {item.sublabel}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            {item.badge && (
                              <span
                                className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                                  isSelected
                                    ? "bg-emerald-700 text-white"
                                    : "bg-slate-200 text-slate-700"
                                }`}
                              >
                                {item.badge}
                              </span>
                            )}
                            {isSelected && <Check className="w-3.5 h-3.5 text-white" />}
                          </div>
                        </button>
                      );
                    })}
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
};
