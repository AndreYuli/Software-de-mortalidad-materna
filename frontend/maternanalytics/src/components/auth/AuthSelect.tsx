import type { LucideIcon } from "lucide-react";
import type { UseFormRegisterReturn } from "react-hook-form";

export interface AuthSelectOption {
  value: string;
  label: string;
}

interface AuthSelectProps {
  id: string;
  label: string;
  icon: LucideIcon;
  error?: string;
  registration: UseFormRegisterReturn;
  options: AuthSelectOption[];
  placeholder: string;
  disabled?: boolean;
}

/** Campo desplegable con la misma estética que AuthField, para selección de afiliación. */
export default function AuthSelect({
  id,
  label,
  icon: Icon,
  error,
  registration,
  options,
  placeholder,
  disabled = false,
}: AuthSelectProps) {
  const errorId = `${id}-error`;

  return (
    <div>
      <label
        htmlFor={id}
        className="mb-1 block text-sm font-medium text-slate-700"
      >
        {label}
      </label>
      <div className="relative">
        <Icon
          className="pointer-events-none absolute left-3 top-1/2 size-5 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <select
          id={id}
          required
          disabled={disabled}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          className={`w-full appearance-none rounded-lg border bg-white py-2.5 pl-10 pr-3 text-slate-900 outline-none transition focus:ring-2 focus:ring-brand-magenta/30 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-400 ${
            error
              ? "border-red-500"
              : "border-slate-300 focus:border-brand-magenta"
          }`}
          {...registration}
        >
          <option value="">{placeholder}</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
      {error && (
        <p id={errorId} className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}
