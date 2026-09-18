from __future__ import annotations
from statistics import mean
from typing import Any

class FundamentalFinancialHealthEngine:
    """FA-METRICS-003 — Financial Health & Balance Sheet Engine."""
    ENGINE_ID="FA-METRICS-003"; VERSION="0.1.0"

    def analyze(self, *, data: Any, statement_history: dict[str, Any]) -> dict[str, Any]:
        h=getattr(data,"financial_health",None); t=getattr(data,"trends",None)
        cash=self._n(getattr(h,"total_cash",None)); debt=self._n(getattr(h,"total_debt",None))
        current=self._n(getattr(h,"current_ratio",None)); quick=self._n(getattr(h,"quick_ratio",None))
        ebitda=self._n(getattr(h,"ebitda",None)); ocf=self._n(getattr(h,"operating_cash_flow",None))
        fcf=self._n(getattr(h,"free_cash_flow",None)); net=self._n(getattr(t,"net_cash",None))
        if net is None and cash is not None and debt is not None: net=cash-debt
        ctd=self._ratio(cash,debt); dte=self._ratio(debt,ebitda)
        liquidity=self._avg([self._band(current,1.5,1.0),self._band(quick,1.2,.8),self._cashdebt(ctd)])
        leverage=self._avg([self._invband(dte,2,4),None if net is None else 85 if net>0 else 25 if net<0 else 50])
        resilience=self._avg([self._flow(ocf),self._flow(fcf),self._history(statement_history)])
        score=self._avg([liquidity,leverage,resilience])
        vals=[cash,debt,net,current,quick,ctd,dte]; avail=sum(v is not None for v in vals)
        return {"engine_id":self.ENGINE_ID,"version":self.VERSION,"status":"operational",
          "balance_sheet":{"cash":cash,"debt":debt,"net_cash":net,"cash_to_debt":ctd,"debt_to_ebitda":dte},
          "liquidity":{"current_ratio":current,"quick_ratio":quick,"score":liquidity,"state":self._state(liquidity)},
          "leverage":{"score":leverage,"state":self._state(leverage)},
          "resilience":{"operating_cash_flow":ocf,"free_cash_flow":fcf,"score":resilience,"state":self._state(resilience)},
          "financial_health_score":score,"financial_health_state":self._state(score),
          "coverage":{"metrics_available":avail,"metrics_total":len(vals),"coverage_pct":round(avail/len(vals)*100,1)},
          "contracts":{"missing_values_not_zero_filled":True,"available_components_only":True,
                       "negative_cash_flow_penalized":True,"net_cash_rewarded":True,
                       "no_investment_decision":True,"no_execution_change":True}}
    def _history(self,h):
        a=h.get("annual") or {}; c=self._series(a,("cash_cash_equivalents_and_short_term_investments","cash_and_cash_equivalents")); d=self._series(a,("total_debt",))
        spreads=[]
        for p in sorted(set(c)&set(d)):
            x,y=self._n(c.get(p)),self._n(d.get(p))
            if x is not None and y is not None: spreads.append(x-y)
        return None if len(spreads)<2 else 75 if spreads[-1]>spreads[-2] else 35 if spreads[-1]<spreads[-2] else 55
    @staticmethod
    def _ratio(a,b): return None if a is None or b in (None,0) else round(a/b,3)
    @staticmethod
    def _band(v,g,w): return None if v is None else 85 if v>=g else 60 if v>=w else 30
    @staticmethod
    def _invband(v,g,w): return None if v is None else 85 if v<=g else 55 if v<=w else 25
    @staticmethod
    def _cashdebt(v): return None if v is None else 90 if v>=1 else 65 if v>=.5 else 35
    @staticmethod
    def _flow(v): return None if v is None else 80 if v>0 else 50 if v==0 else 20
    @staticmethod
    def _state(v): return "UNAVAILABLE" if v is None else "STRONG" if v>=80 else "GOOD" if v>=65 else "MODERATE" if v>=50 else "WEAK"
    @staticmethod
    def _avg(v):
        x=[i for i in v if i is not None]; return round(mean(x),1) if x else None
    @staticmethod
    def _series(p,aliases):
        for st in p.values():
            m=(st or {}).get("metrics") or {}; low={str(k).lower():v for k,v in m.items()}
            for a in aliases:
                if a.lower() in low:return low[a.lower()] or {}
        return {}
    @staticmethod
    def _n(v):
        if v is None or isinstance(v,bool):return None
        try:
            x=float(v); return None if x!=x else x
        except (TypeError,ValueError):return None
