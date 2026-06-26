class HotspotAnalysisService:
    def analyze(self, incidents):
        return {"clusters": [], "source_count": len(incidents)}

    def heatmap(self, incidents):
        return {"points": [], "source_count": len(incidents)}


hotspot_analysis_service = HotspotAnalysisService()
