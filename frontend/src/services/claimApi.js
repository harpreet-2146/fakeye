export async function checkClaim(claim) {
  const res = await fetch("/api/check-claim", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ claim }),
  });

  return res.json();
}
