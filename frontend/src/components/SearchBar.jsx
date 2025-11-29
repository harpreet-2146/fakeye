import React, { useState } from "react";

export default function SearchBar({ onSearch, defaultValue="", loading=false }){
  const [value, setValue] = useState(defaultValue);

  function submit(e){
    e?.preventDefault();
    if(!value?.trim()) return;
    onSearch(value.trim());
  }

  return (
    <form onSubmit={submit} className="flex gap-3">
      <input
        value={value}
        onChange={(e)=>setValue(e.target.value)}
        placeholder="e.g. Indira Gandhi was killed by Muslims"
        className="flex-1 p-4 rounded-3xl neu-inset outline-none placeholder:text-slate-500 text-sm"
      />
      <button
        type="submit"
        className="px-6 py-3 rounded-3xl neu text-sm font-medium"
        disabled={loading}
      >
        {loading ? "Checking…" : "Check Claim"}
      </button>
    </form>
  );
}
