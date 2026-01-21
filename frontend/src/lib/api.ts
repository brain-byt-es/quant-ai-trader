// Define the base URL for the API
const BASE_URL = "/api/py";

export class ApiClient {
  private static instance: ApiClient;
  private baseUrl: string;

  private constructor() {
    this.baseUrl = BASE_URL;
  }

  public static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  private async fetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`;
    
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    });

    if (!res.ok) {
      const errorBody = await res.json().catch(() => ({}));
      throw new Error(errorBody.detail || `API call failed: ${res.statusText}`);
    }

    return res.json();
  }

  public async getPortfolioStats() {
    return this.fetch<{
      equity: number;
      buying_power: number;
      day_change_percent: number;
    }>("/portfolio/stats");
  }

  public async getPositions() {
    return this.fetch<{
      positions: Array<{
        ticker: string;
        qty: number;
        market_value: number;
        cost_basis: number;
        unrealized_pl: number;
        unrealized_plpc: number;
      }>;
    }>("/portfolio/positions");
  }

  public async getMarketStatus() {
    return this.fetch<{ is_open: boolean; next_open: string }>("/market-status");
  }
  
  public async getFactorAnalysis(ticker: string) {
    return this.fetch<{
      value_score: number;
      quality_score: number;
      momentum_score: number;
      growth_score: number;
      risk_score: number;
    }>(`/analysis/factors/${ticker}`);
  }

  public streamAnalysis(ticker: string, market?: string, k?: number): EventSource {
    const params = new URLSearchParams();
    if (market) params.append("market", market);
    if (k) params.append("k", k.toString());
    
    const queryString = params.toString();
    const url = `${this.baseUrl}/analysis/stream/${ticker}${queryString ? `?${queryString}` : ""}`;
    
    console.log(`ApiClient: Opening stream to ${url}`);
    return new EventSource(url, { withCredentials: true });
  }

  public async triggerKillSwitch() {
    return this.fetch<{ status: string; message: string }>("/trading/kill-switch", {
      method: "POST"
    });
  }

  public async getHealth() {
    return this.fetch<{ status: string; services: Record<string, string> }>("/health");
  }
}

export const api = ApiClient.getInstance();
