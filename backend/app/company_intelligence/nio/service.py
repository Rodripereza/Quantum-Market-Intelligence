from app.company_intelligence.nio.collector import NioDeliveryCollector
from app.company_intelligence.nio.delivery_engine import NioDeliveryIntelligenceEngine
from app.company_intelligence.nio.asp_engine import NioAspRevenueEngine
from app.company_intelligence.nio.momentum_engine import NioDeliveryMomentumEngine
from app.company_intelligence.nio.schemas import NioDeliveryResponse

class NioDeliveryService:
    def __init__(self):
        self.collector = NioDeliveryCollector()
        self.engine = NioDeliveryIntelligenceEngine()
        self.asp_engine = NioAspRevenueEngine()
        self.momentum_engine = NioDeliveryMomentumEngine()

    def analyze(self):
        records = self.collector.collect()
        snapshot, intelligence = self.engine.analyze(records)
        asp_intelligence = self.asp_engine.analyze(records)
        delivery_momentum = self.momentum_engine.analyze(records, asp_intelligence)
        return NioDeliveryResponse(
            snapshot=snapshot,
            intelligence=intelligence,
            asp_intelligence=asp_intelligence,
            delivery_momentum=delivery_momentum,
            monthly=records,
        )
