class OrderedList(list):
    def __init__(self, generator):
        super().__init__(generator)
        self.sort(key=lambda p: p.id)

    def sort_by_importance(self):
        self.sort(key=lambda p: p.importance)

    def sort_by_urgency(self):
        self.sort(key=lambda p: p.urgency)