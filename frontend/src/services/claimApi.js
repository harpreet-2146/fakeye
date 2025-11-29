export async function checkClaim(claim){
  const res = await fetch("/api/check-claim", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim })
  });
  if(!res.ok){
    const txt = await res.text();
    throw new Error(txt || "Server error");
  }
  return res.json();
}
