class PhotoDanger:
    @staticmethod
    def assess_threat(target):
        """
        Görsel veriyi analiz eder.
        Hedef bir 'Kaotropi' ise True döner.
        """
        # Hedefin kimliğinde 'kaotropi' stringi geçiyorsa tehdittir
        return "kaotropi" in target.uid
