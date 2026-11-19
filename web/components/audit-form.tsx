"use client";

import { useActionState, useId } from "react";
import type { AuditFormError, AuditFormState } from "@/app/[lang]/actions";

type AuditFormLabels = {
  urlLabel: string;
  placeholder: string;
  submit: string;
  pending: string;
  errors: Record<AuditFormError, string>;
};

type AuditFormProps = {
  action: (state: AuditFormState, formData: FormData) => Promise<AuditFormState>;
  labels: AuditFormLabels;
  variant: "hero" | "compact";
  initialUrl?: string;
};

const VARIANT_CLASSES = {
  hero: {
    form: "w-full max-w-3xl rounded-2xl border border-slate-200 bg-white p-2.5 shadow-[0_10px_30px_rgba(15,23,42,0.08)]",
    input: "h-13 rounded-lg px-4 text-[17px]",
    button: "h-13 px-6 text-base",
  },
  compact: {
    form: "w-full max-w-xl",
    input: "h-11 rounded-[10px] border border-slate-300 bg-white px-3.5 text-[15px]",
    button: "h-11 px-4 text-[15px]",
  },
};

export function AuditForm({ action, labels, variant, initialUrl = "" }: AuditFormProps) {
  const [state, formAction, isPending] = useActionState(action, { error: null, url: initialUrl });
  const inputId = useId();
  const errorId = useId();
  const classes = VARIANT_CLASSES[variant];

  return (
    <form action={formAction} className={classes.form}>
      <div className="flex flex-wrap items-center gap-2.5">
        <label htmlFor={inputId} className="sr-only">
          {labels.urlLabel}
        </label>
        <input
          key={state.url}
          id={inputId}
          name="url"
          type="text"
          inputMode="url"
          autoComplete="url"
          spellCheck={false}
          required
          defaultValue={state.url}
          placeholder={labels.placeholder}
          aria-invalid={state.error === "invalid_url" ? true : undefined}
          aria-describedby={state.error ? errorId : undefined}
          className={`min-w-0 flex-[1_1_280px] text-ink placeholder:text-slate-500 ${classes.input}`}
        />
        <button
          type="submit"
          disabled={isPending}
          className={`inline-flex min-w-11 items-center justify-center gap-2 rounded-[10px] bg-accent font-semibold text-white hover:bg-blue-800 disabled:cursor-wait disabled:opacity-80 ${classes.button}`}
        >
          {isPending ? labels.pending : labels.submit}
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.2"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <path d="M5 12h14M13 6l6 6-6 6" />
          </svg>
        </button>
      </div>
      {state.error ? (
        <p id={errorId} role="alert" className="mt-2 px-2 text-left text-sm font-medium text-poor">
          {labels.errors[state.error]}
        </p>
      ) : null}
    </form>
  );
}
