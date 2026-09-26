from app.tools.base import ToolBase
from pydantic import BaseModel
import ast
import operator
import math

class CalculatorTool(ToolBase):
    name = "calculator"
    description = "Safely evaluates simple mathematical expressions."
    
    class InputSchema(BaseModel):
        expression: str
        
    class OutputSchema(BaseModel):
        expression: str
        value: float
        
    def __init__(self):
        self.operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Pow: operator.pow,
            ast.USub: operator.neg
        }
        
    def _eval_node(self, node):
        if isinstance(node, ast.Num):
            return node.n
        elif isinstance(node, ast.BinOp):
            return self.operators[type(node.op)](self._eval_node(node.left), self._eval_node(node.right))
        elif isinstance(node, ast.UnaryOp):
            return self.operators[type(node.op)](self._eval_node(node.operand))
        else:
            raise TypeError(node)

    async def execute(self, input_data: InputSchema) -> OutputSchema:
        try:
            node = ast.parse(input_data.expression, mode='eval').body
            result = self._eval_node(node)
            return self.OutputSchema(expression=input_data.expression, value=float(result))
        except ZeroDivisionError:
            raise ValueError("Division by zero")
        except Exception as e:
            raise ValueError(f"Invalid math expression: {input_data.expression}")
