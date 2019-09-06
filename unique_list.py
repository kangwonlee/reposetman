import collections


class unique_list(collections.UserList):
    def __init__(self, *args, **kwargs):
        super(unique_list, self).__init__(*args, **kwargs)

    def add(self, item):
        if not (item in self.data):
            self.data.append(item)

    def update(self, other):
        self.data.extend(other)
        temp_set = set(self.data)
        self.data = list(temp_set)
        del temp_set
