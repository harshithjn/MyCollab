from typing import Dict, List, Any, Optional
import uuid
from datetime import datetime
from operational_transform import Operation

class Document:
    def __init__(self, doc_id: str, initial_content: str = ""):
        self.doc_id = doc_id
        self.content = initial_content
        self.version = 0
        self.operations: List[List] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.language = "javascript"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_id": self.doc_id,
            "content": self.content,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "language": self.language,
            "operations": [[op.to_dict() if hasattr(op, 'to_dict') else op for op in ops] for ops in self.operations]
        }
    
    def apply_operation(self, operation: List, new_content: str) -> int:
        self.operations.append(operation)
        self.content = new_content
        self.version += 1
        self.updated_at = datetime.now()
        return self.version

class DocumentManager:
    def __init__(self):
        self.documents: Dict[str, Document] = {}
    
    def create_document(self, doc_id: str = None, initial_content: str = "", language: str = "javascript") -> str:
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        
        if doc_id in self.documents:
            raise ValueError(f"Document {doc_id} already exists")
        
        doc = Document(doc_id, initial_content)
        doc.language = language
        self.documents[doc_id] = doc
        return doc_id
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        if doc_id not in self.documents:
            return None
        
        return self.documents[doc_id].to_dict()
    
    def update_document(self, doc_id: str, content: str, language: str = None) -> int:
        if doc_id not in self.documents:
            return 0
        
        doc = self.documents[doc_id]
        doc.content = content
        doc.version += 1
        doc.updated_at = datetime.now()
        
        if language:
            doc.language = language
        
        return doc.version
    
    def apply_operation(self, doc_id: str, operation: List, new_content: str) -> int:
        if doc_id not in self.documents:
            raise ValueError(f"Document {doc_id} not found")
        
        return self.documents[doc_id].apply_operation(operation, new_content)
    
    def delete_document(self, doc_id: str) -> bool:
        if doc_id in self.documents:
            del self.documents[doc_id]
            return True
        return False
    
    def list_documents(self) -> List[Dict[str, Any]]:
        return [doc.to_dict() for doc in self.documents.values()]
    
    def get_document_history(self, doc_id: str) -> Optional[List[Dict[str, Any]]]:
        if doc_id not in self.documents:
            return None
        
        doc = self.documents[doc_id]
        history = []
        
        for i, ops in enumerate(doc.operations):
            history.append({
                "version": i + 1,
                "operations": [op.to_dict() for op in ops],
                "timestamp": doc.updated_at.isoformat()
            })
        
        return history
    
    def get_document_at_version(self, doc_id: str, version: int) -> Optional[str]:
        if doc_id not in self.documents:
            return None
        
        doc = self.documents[doc_id]
        if version > doc.version or version < 0:
            return None
        
        return doc.content
    
    def set_document_language(self, doc_id: str, language: str) -> bool:
        if doc_id not in self.documents:
            return False
        
        self.documents[doc_id].language = language
        return True
    
    def get_document_stats(self, doc_id: str) -> Optional[Dict[str, Any]]:
        if doc_id not in self.documents:
            return None
        
        doc = self.documents[doc_id]
        return {
            "doc_id": doc_id,
            "content_length": len(doc.content),
            "line_count": len(doc.content.split('\n')),
            "version": doc.version,
            "operation_count": len(doc.operations),
            "created_at": doc.created_at.isoformat(),
            "updated_at": doc.updated_at.isoformat(),
            "language": doc.language
        }