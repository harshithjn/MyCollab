from typing import List, Dict, Any, Tuple
import json

class Operation:
    def __init__(self, type: str, value: Any = None, length: int = 0):
        self.type = type
        self.value = value
        self.length = length
    
    def to_dict(self):
        return {
            "type": self.type,
            "value": self.value,
            "length": self.length
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(data["type"], data.get("value"), data.get("length", 0))

class OperationalTransform:
    def __init__(self):
        pass
    
    def create_operation(self, old_text: str, new_text: str, cursor_pos: int = None) -> List[Operation]:
        operations = []
        
        i = 0
        while i < len(old_text) and i < len(new_text):
            if old_text[i] == new_text[i]:
                operations.append(Operation("retain", length=1))
                i += 1
            else:
                break
        
        if i < len(old_text):
            operations.append(Operation("delete", length=len(old_text) - i))
        
        if i < len(new_text):
            operations.append(Operation("insert", value=new_text[i:]))
        
        return operations
    
    def apply_operation(self, text: str, operations: List) -> str:
        result = ""
        pos = 0
        
        for op in operations:
            if isinstance(op, dict):
                op_type = op.get("type")
                op_length = op.get("length", 0)
                op_value = op.get("value", "")
            else:
                op_type = op.type
                op_length = op.length
                op_value = op.value
            
            if op_type == "retain":
                if pos + op_length > len(text):
                    raise ValueError("Retain operation exceeds text length")
                result += text[pos:pos + op_length]
                pos += op_length
            elif op_type == "insert":
                result += op_value
            elif op_type == "delete":
                pos += op_length
        
        result += text[pos:]
        return result
    
    def transform_operation(self, operation: List, 
                          concurrent_operations: List[List], 
                          base_version: int) -> List:
        transformed_ops = operation.copy()
        
        for concurrent_op in concurrent_operations:
            transformed_ops = self._transform_against_operation(transformed_ops, concurrent_op)
        
        return transformed_ops
    
    def _transform_against_operation(self, op1: List, op2: List) -> List:
        result = []
        i1 = i2 = 0
        
        while i1 < len(op1) and i2 < len(op2):
            op1_curr = op1[i1]
            op2_curr = op2[i2]
            
            if isinstance(op1_curr, dict):
                op1_type = op1_curr.get("type")
                op1_length = op1_curr.get("length", 0)
                op1_value = op1_curr.get("value", "")
            else:
                op1_type = op1_curr.type
                op1_length = op1_curr.length
                op1_value = op1_curr.value
                
            if isinstance(op2_curr, dict):
                op2_type = op2_curr.get("type")
                op2_length = op2_curr.get("length", 0)
                op2_value = op2_curr.get("value", "")
            else:
                op2_type = op2_curr.type
                op2_length = op2_curr.length
                op2_value = op2_curr.value
            
            if op1_type == "insert":
                result.append(op1_curr)
                i1 += 1
            elif op2_type == "insert":
                if op1_type == "retain":
                    if isinstance(op1_curr, dict):
                        op1_curr["length"] += len(op2_value)
                    else:
                        op1_curr.length += len(op2_value)
                elif op1_type == "delete":
                    result.append({"type": "retain", "length": len(op2_value)})
                    result.append(op1_curr)
                i2 += 1
            elif op1_type == "retain" and op2_type == "retain":
                min_len = min(op1_length, op2_length)
                result.append({"type": "retain", "length": min_len})
                
                if isinstance(op1_curr, dict):
                    op1_curr["length"] -= min_len
                else:
                    op1_curr.length -= min_len
                    
                if isinstance(op2_curr, dict):
                    op2_curr["length"] -= min_len
                else:
                    op2_curr.length -= min_len
                
                if (isinstance(op1_curr, dict) and op1_curr["length"] == 0) or (not isinstance(op1_curr, dict) and op1_curr.length == 0):
                    i1 += 1
                if (isinstance(op2_curr, dict) and op2_curr["length"] == 0) or (not isinstance(op2_curr, dict) and op2_curr.length == 0):
                    i2 += 1
            elif op1_type == "retain" and op2_type == "delete":
                min_len = min(op1_length, op2_length)
                
                if isinstance(op1_curr, dict):
                    op1_curr["length"] -= min_len
                else:
                    op1_curr.length -= min_len
                    
                if isinstance(op2_curr, dict):
                    op2_curr["length"] -= min_len
                else:
                    op2_curr.length -= min_len
                
                if (isinstance(op1_curr, dict) and op1_curr["length"] == 0) or (not isinstance(op1_curr, dict) and op1_curr.length == 0):
                    i1 += 1
                if (isinstance(op2_curr, dict) and op2_curr["length"] == 0) or (not isinstance(op2_curr, dict) and op2_curr.length == 0):
                    i2 += 1
            elif op1_type == "delete" and op2_type == "retain":
                result.append(op1_curr)
                i1 += 1
            elif op1_type == "delete" and op2_type == "delete":
                min_len = min(op1_length, op2_length)
                
                if isinstance(op1_curr, dict):
                    op1_curr["length"] -= min_len
                else:
                    op1_curr.length -= min_len
                    
                if isinstance(op2_curr, dict):
                    op2_curr["length"] -= min_len
                else:
                    op2_curr.length -= min_len
                
                if (isinstance(op1_curr, dict) and op1_curr["length"] == 0) or (not isinstance(op1_curr, dict) and op1_curr.length == 0):
                    i1 += 1
                if (isinstance(op2_curr, dict) and op2_curr["length"] == 0) or (not isinstance(op2_curr, dict) and op2_curr.length == 0):
                    i2 += 1
        
        while i1 < len(op1):
            result.append(op1[i1])
            i1 += 1
        
        return result
    
    def compose_operations(self, op1: List[Operation], op2: List[Operation]) -> List[Operation]:
        return op1 + op2
    
    def invert_operation(self, operation: List[Operation], text: str) -> List[Operation]:
        inverted = []
        pos = 0
        
        for op in operation:
            if op.type == "retain":
                inverted.append(Operation("retain", length=op.length))
                pos += op.length
            elif op.type == "insert":
                inverted.append(Operation("delete", length=len(op.value)))
            elif op.type == "delete":
                inverted.append(Operation("insert", value=text[pos:pos + op.length]))
                pos += op.length
        
        return inverted