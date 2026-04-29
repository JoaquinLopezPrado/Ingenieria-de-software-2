from datetime import date
from typing import Optional


class DocumentType:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class ClientProfile:
    def __init__(
        self,
        id: int,
        user_id: int,
        first_name: str,
        last_name: str,
        phone: str,
        birth_date: date,
        document_type: DocumentType,
        doc_number: str,
    ):
        self.id = id
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.phone = phone
        self.birth_date = birth_date
        self.document_type = document_type
        self.doc_number = doc_number


class EmployeeProfile:
    def __init__(
        self,
        id: int,
        user_id: int,
        first_name: str,
        last_name: str,
        internal_file_number: Optional[str] = None,
    ):
        self.id = id
        self.user_id = user_id
        self.first_name = first_name
        self.last_name = last_name
        self.internal_file_number = internal_file_number
