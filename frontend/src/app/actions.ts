"use server";

export async function executeTradeAction(token: string, tradeDetails: { ticker: string }) {
  const backendUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
  const url = `${backendUrl}/api/v1/trades/approve/${token}`;

  console.log(`[Server Action] Approving trade token: ${token} via ${url}`);

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      }
    });

    if (!response.ok) {
      const errorData = (await response.json().catch(() => ({ detail: response.statusText }))) as { detail?: string };
      return { 
        success: false, 
        message: `Backend Error: ${errorData.detail || "Failed to execute trade"}` 
      };
    }

    const result = await response.json();
    return { 
      success: true, 
      message: `Trade ${tradeDetails.ticker} executed: ${result.message || "Success"}` 
    };

  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : "Could not reach Quant Engine";
    console.error("Trade execution error:", error);
    return { 
      success: false, 
      message: `Connection Error: ${errorMessage}` 
    };
  }
}