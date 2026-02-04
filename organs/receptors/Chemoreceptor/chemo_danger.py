class ChemoDanger:
    @staticmethod
    def assess_threat(trail_point):
        """
        Koku izini analiz eder.
        İzin sahibi bir Kaotropi ise True döner.
        """
        return "kaotropi" in trail_point.owner_uid
