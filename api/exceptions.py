

class WorkflowExistsPatchNotAllowedException(Exception):

    def __init__(self):
        self.msg = "Object in Approval / Already Approved, can't allow edit"
        super().__init__(self.msg)
