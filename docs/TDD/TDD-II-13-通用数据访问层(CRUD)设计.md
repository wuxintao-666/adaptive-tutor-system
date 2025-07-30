### **技术设计文档 (TDD-II-13): 通用数据访问层 (CRUD) 设计**

**版本:** 1.2
**关联的顶层TDD:** V1.2 - 章节 3.1 (数据库设计)
**作者:** 曹欣卓
**日期:** 2025-7-30

---

#### **1. 功能概述 (Feature Overview)**

**目标:**
为项目的所有数据模型（如 `Participant`, `EventLog`, `UserProgress` 等）提供一套标准化的、可复用的CRUD（创建、读取、更新、删除）操作接口。通过设计一个通用的 `CRUDBase` 基类，最大限度地消除重复的样板代码，提高开发效率和代码一致性。

**核心原则:**
*   **DRY (Don't Repeat Yourself):** 将所有模型共有的数据操作逻辑（如按ID获取、获取列表、创建、更新、删除）只实现一次。
*   **标准化 (Standardization):** 确保所有数据表的CRUD操作都遵循相同的接口和命名约定。
*   **可扩展性 (Extensibility):** 基类提供通用方法，而具体的CRUD类可以轻松地继承并添加针对特定模型的查询方法（如 `get_by_username`）。

**范围:**
1.  设计并实现一个通用的 `CRUDBase` 类，使用Python的泛型来适应不同的SQLAlchemy模型和Pydantic Schema。
2.  规范具体的CRUD类（如 `crud_participant`）如何继承和使用 `CRUDBase`。
3.  明确此设计对现有代码的重构路径。

---

#### **2. 设计与实现**

##### **2.1. 通用基类 `CRUDBase` 设计**

我们将创建一个位于 `backend/app/crud/base.py` 的新文件，用于存放 `CRUDBase`。

这个设计的核心是利用Python的 `typing` 模块中的 `TypeVar` 和 `Generic`。这允许我们创建一个“占位符”类型，使得这个基类可以与任何模型和Schema配合使用，同时保持完整的类型提示和静态检查支持。

*   `ModelType`: 代表SQLAlchemy模型类 (例如 `Participant`)。
*   `CreateSchemaType`: 代表用于创建记录的Pydantic模型 (例如 `ParticipantCreate`)。
*   `UpdateSchemaType`: 代表用于更新记录的Pydantic模型 (例如 `ParticipantUpdate`)。

##### **2.2. `CRUDBase` 代码实现**

```python
# backend/app/crud/base.py
import json
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 假设你的SQLAlchemy模型基类在 app.db.base_class.Base
from app.db.base_class import Base 

# 定义泛型类型变量
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        """
        CRUD object with default methods to Create, Read, Update, Delete (CRUD).

        **Parameters**

        * `model`: A SQLAlchemy model class
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """通过ID获取单个记录。"""
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """获取多个记录（支持分页）。"""
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """创建一个新的记录。"""
        # 使用fastapi的jsonable_encoder，确保数据可被序列化
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)  # SQLAlchemy model
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """更新一个已存在的记录。"""
        obj_data = jsonable_encoder(db_obj)
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            # exclude_unset=True 表示只获取被显式设置了值的字段
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
                
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Optional[ModelType]:
        """删除一个记录。"""
        obj = db.query(self.model).get(id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj

```

##### **2.3. 具体CRUD类的实现 (示例)**

有了 `CRUDBase` 之后，我们现有的 `crud_participant.py` 文件就可以被极大地简化。它只需要继承基类，并定义那些**非通用**的、`Participant` 模型特有的查询方法即可。

```python
# backend/app/crud/crud_participant.py
from typing import Optional

from sqlalchemy.orm import Session

from .base import CRUDBase  # 导入新的基类
from app.models.participant import Participant
from app.schemas.participant import ParticipantCreate, ParticipantUpdate # 假设这些Schema已定义

class CRUDParticipant(CRUDBase[Participant, ParticipantCreate, ParticipantUpdate]):
    def get_by_username(self, db: Session, *, username: str) -> Optional[Participant]:
        """通过username获取参与者。这是一个Participant模型特有的查询。"""
        return db.query(Participant).filter(Participant.username == username).first()

# 创建一个该类的单例，供API层导入和使用
participant = CRUDParticipant(Participant)
```

如上所示，`CRUDParticipant` 类现在非常简洁。它自动获得了 `get`, `get_multi`, `create`, `update`, `remove` 所有方法，并且只添加了自己需要的 `get_by_username`。

---

#### **3. 对现有代码的影响 (Impact on Existing Code)**

1.  **创建新文件:**
    *   在 `backend/app/crud/` 目录下创建 `base.py` 文件，并将 `CRUDBase` 的代码放入其中。

2.  **重构现有CRUD文件:**
    *   修改 `backend/app/crud/crud_participant.py`，使其继承 `CRUDBase`，如 **2.3** 节所示。
    *   对项目中所有其他的CRUD文件（如 `crud_progress.py`, `crud_event.py` 等）进行类似的重构。它们都将继承 `CRUDBase` 并只保留特有的查询方法。

3.  **Schema文件:**
    *   需要确保每个模型都有对应的 `Create` 和 `Update` Pydantic Schema。例如，`app/schemas/participant.py` 中应有 `ParticipantCreate` 和 `ParticipantUpdate`。

4.  **API层 (无影响):**
    *   API端点的代码**无需任何改动**。因为我们导出的实例名称不变（`participant`），并且方法签名保持兼容。例如，`endpoints/session.py` 中调用的 `crud_participant.get_by_username(...)` 和 `crud_participant.create(...)` 依然有效。

---

#### **4. 总结 (Conclusion)**

引入 `CRUDBase` 是一个一劳永逸的架构优化。它通过抽象和泛型，将数据访问层的通用逻辑与特定逻辑完美分离。

**带来的好处:**
*   **代码量显著减少:** 无需为每个模型重复编写相同的CRUD函数。
*   **可维护性增强:** 所有通用CRUD逻辑集中在一处，修复bug或增加功能只需修改一个文件。
*   **开发速度加快:** 为新模型添加数据访问层变得极其迅速，只需创建一个继承 `CRUDBase` 的子类即可。
*   **代码更加健壮:** 标准化的接口和完整的类型提示减少了出错的可能性。

这个设计为项目未来的扩展和维护奠定了坚实的基础。
