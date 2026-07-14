"""
数据库模型定义模块
业务负责制：本模块负责所有核心数据对象的定义与数据库初始化
数据同源：所有数据以此模块定义的表结构为唯一权威来源
"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Text,
    ForeignKey, DateTime, Boolean, Enum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import enum

# ==================== 数据库引擎配置 ====================
DATABASE_URL = "sqlite:///parts_cost.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==================== 枚举类型 ====================
class PartStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PROTOTYPE = "prototype"
    OBSOLETE = "obsolete"


# ==================== 基础配置数据模型 ====================
# 统一语言：以下配置项是系统的"统一语言"，所有引用都通过外键关联

class Currency(Base):
    """货币配置 - 基础参考数据"""
    __tablename__ = "currencies"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False, comment="货币代码，如 CNY/USD/EUR")
    name = Column(String(50), nullable=False, comment="货币名称")
    symbol = Column(String(10), nullable=False, comment="货币符号，如 ¥/$")
    description = Column(Text, comment="备注说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    cost_items = relationship("CostItem", back_populates="currency")


class Unit(Base):
    """单位配置 - 基础参考数据"""
    __tablename__ = "units"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, comment="单位代码，如 kg/pcs/m")
    name = Column(String(50), nullable=False, comment="单位名称")
    category = Column(String(30), comment="单位类别：重量/数量/长度/体积")
    description = Column(Text, comment="备注说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    parts = relationship("Part", back_populates="weight_unit")


class Region(Base):
    """区域配置 - 基础参考数据"""
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, comment="区域代码")
    name = Column(String(50), nullable=False, comment="区域名称")
    country = Column(String(50), comment="所属国家")
    description = Column(Text, comment="备注说明")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    parts = relationship("Part", back_populates="origin_region")


class MaterialType(Base):
    """物料类型配置 - 基础参考数据"""
    __tablename__ = "material_types"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, comment="物料类型代码")
    name = Column(String(50), nullable=False, comment="物料类型名称")
    description = Column(Text, comment="类型描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    parts = relationship("Part", back_populates="material_type")


# ==================== 核心业务对象 ====================

class Part(Base):
    """
    零件主数据 - 核心业务对象
    业务对象：Part是系统的核心业务对象，围绕业务需求设计
    数据同源：零件信息是单一权威数据源
    """
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    part_code = Column(String(50), unique=True, nullable=False, comment="零件编码（唯一标识）")
    name = Column(String(100), nullable=False, comment="零件名称")
    description = Column(Text, comment="零件描述")
    version = Column(String(20), default="1.0", comment="版本号")
    status = Column(String(20), default=PartStatus.ACTIVE, comment="零件状态：active/inactive/prototype/obsolete")

    # 外键关联（统一语言：禁止硬编码，必须通过外键）
    material_type_id = Column(Integer, ForeignKey("material_types.id"), comment="物料类型（外键）")
    weight_unit_id = Column(Integer, ForeignKey("units.id"), comment="重量单位（外键）")
    origin_region_id = Column(Integer, ForeignKey("regions.id"), comment="来源区域（外键）")

    # 物理属性
    weight = Column(Float, comment="重量")
    drawing_number = Column(String(50), comment="图纸编号")
    supplier = Column(String(100), comment="供应商")

    # 生命周期管理
    created_by = Column(String(50), default="system", comment="创建人")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    material_type = relationship("MaterialType", back_populates="parts")
    weight_unit = relationship("Unit", back_populates="parts")
    origin_region = relationship("Region", back_populates="parts")
    cost_items = relationship("CostItem", back_populates="part", cascade="all, delete-orphan")

    # BOM关联
    bom_as_parent = relationship("BOM", foreign_keys="BOM.parent_part_id", back_populates="parent_part", cascade="all, delete-orphan")
    bom_as_child = relationship("BOM", foreign_keys="BOM.child_part_id", back_populates="child_part")


# ==================== 事务数据 ====================

class BOM(Base):
    """
    物料清单 (Bill of Materials) - 事务数据
    事务数据：BOM通过调用Part主数据建立零件间的层级关系
    数据联接：体现了"管理好事务数据对主数据的调用"的治理思想
    """
    __tablename__ = "boms"

    id = Column(Integer, primary_key=True, index=True)
    parent_part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, comment="父零件ID（外键）")
    child_part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, comment="子零件ID（外键）")
    quantity = Column(Float, nullable=False, default=1.0, comment="用量")
    unit_id = Column(Integer, ForeignKey("units.id"), comment="用量单位（外键）")
    bom_level = Column(Integer, default=1, comment="BOM层级")
    effective_date = Column(DateTime, default=datetime.utcnow, comment="生效日期")
    expiry_date = Column(DateTime, comment="失效日期")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    parent_part = relationship("Part", foreign_keys=[parent_part_id], back_populates="bom_as_parent")
    child_part = relationship("Part", foreign_keys=[child_part_id], back_populates="bom_as_child")
    unit = relationship("Unit")


# ==================== 报告数据 ====================

class CostItem(Base):
    """
    成本项 - 报告数据
    报告数据：成本计算结果用于支持业务决策（定价、成本优化）
    计算逻辑和数据来源必须清晰、可追溯
    """
    __tablename__ = "cost_items"

    id = Column(Integer, primary_key=True, index=True)
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False, comment="零件ID（外键）")
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False, comment="货币ID（外键）")

    # 成本构成（材料 + 制造 + 间接 = 总成本）
    material_cost = Column(Float, default=0.0, comment="材料成本")
    manufacturing_cost = Column(Float, default=0.0, comment="制造成本")
    overhead_cost = Column(Float, default=0.0, comment="间接费用")
    total_cost = Column(Float, default=0.0, comment="总成本 = 材料+制造+间接")

    # 成本追溯信息
    cost_version = Column(String(20), default="v1.0", comment="成本版本")
    calculation_basis = Column(Text, comment="计算依据（可追溯）")
    effective_date = Column(DateTime, default=datetime.utcnow, comment="生效日期")
    notes = Column(Text, comment="备注")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联关系
    part = relationship("Part", back_populates="cost_items")
    currency = relationship("Currency", back_populates="cost_items")


# ==================== 初始化函数 ====================

def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话（依赖注入模式）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_data():
    """填充初始演示数据"""
    db = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(Currency).count() > 0:
            return

        # 货币数据
        currencies = [
            Currency(code="CNY", name="人民币", symbol="¥", description="中国法定货币"),
            Currency(code="USD", name="美元", symbol="$", description="美国法定货币"),
            Currency(code="EUR", name="欧元", symbol="€", description="欧盟法定货币"),
            Currency(code="JPY", name="日元", symbol="¥", description="日本法定货币"),
        ]
        db.add_all(currencies)

        # 单位数据
        units = [
            Unit(code="pcs", name="件", category="数量", description="个数计量"),
            Unit(code="kg", name="千克", category="重量", description="重量计量"),
            Unit(code="g", name="克", category="重量", description="重量计量"),
            Unit(code="m", name="米", category="长度", description="长度计量"),
            Unit(code="mm", name="毫米", category="长度", description="长度计量"),
            Unit(code="L", name="升", category="体积", description="体积计量"),
        ]
        db.add_all(units)

        # 区域数据
        regions = [
            Region(code="CN-EAST", name="华东区", country="中国", description="上海、江苏、浙江等"),
            Region(code="CN-SOUTH", name="华南区", country="中国", description="广东、广西、海南等"),
            Region(code="CN-NORTH", name="华北区", country="中国", description="北京、天津、河北等"),
            Region(code="US-WEST", name="美国西部", country="美国", description="加州、华盛顿州等"),
            Region(code="EU-CENT", name="欧洲中部", country="欧盟", description="德国、法国等"),
        ]
        db.add_all(regions)

        # 物料类型数据
        material_types = [
            MaterialType(code="RAW", name="原材料", description="未经加工的基础材料"),
            MaterialType(code="SEMI", name="半成品", description="经过部分加工的零件"),
            MaterialType(code="FINISH", name="成品件", description="完整制成的零件"),
            MaterialType(code="PURCHASE", name="外购件", description="从外部供应商采购的零件"),
            MaterialType(code="STANDARD", name="标准件", description="符合国家/行业标准的零件"),
        ]
        db.add_all(material_types)

        db.commit()

        # 创建示例零件
        pcs_unit = db.query(Unit).filter_by(code="pcs").first()
        kg_unit = db.query(Unit).filter_by(code="kg").first()
        raw_type = db.query(MaterialType).filter_by(code="RAW").first()
        semi_type = db.query(MaterialType).filter_by(code="SEMI").first()
        finish_type = db.query(MaterialType).filter_by(code="FINISH").first()
        east_region = db.query(Region).filter_by(code="CN-EAST").first()
        cny = db.query(Currency).filter_by(code="CNY").first()

        parts = [
            Part(
                part_code="P-001",
                name="主传动轴",
                description="发动机主传动轴，高强度钢材制成",
                version="2.1",
                status="active",
                material_type_id=finish_type.id,
                weight_unit_id=kg_unit.id,
                origin_region_id=east_region.id,
                weight=5.2,
                drawing_number="DWG-2023-001",
                supplier="华东精密机械有限公司"
            ),
            Part(
                part_code="P-002",
                name="轴承座",
                description="支撑传动轴的轴承座，铸铁材质",
                version="1.5",
                status="active",
                material_type_id=semi_type.id,
                weight_unit_id=kg_unit.id,
                origin_region_id=east_region.id,
                weight=2.8,
                drawing_number="DWG-2023-002",
                supplier="江苏铸造工业股份"
            ),
            Part(
                part_code="P-003",
                name="深沟球轴承",
                description="6205型深沟球轴承，标准件",
                version="1.0",
                status="active",
                material_type_id=raw_type.id,
                weight_unit_id=kg_unit.id,
                origin_region_id=east_region.id,
                weight=0.15,
                drawing_number="STD-6205",
                supplier="SKF上海"
            ),
            Part(
                part_code="P-004",
                name="密封圈",
                description="橡胶密封圈，防尘防油",
                version="1.2",
                status="active",
                material_type_id=raw_type.id,
                weight_unit_id=kg_unit.id,
                origin_region_id=east_region.id,
                weight=0.02,
                drawing_number="STD-SEAL-001",
                supplier="宁波橡塑制品"
            ),
            Part(
                part_code="P-005",
                name="传动轴组件",
                description="完整传动轴装配组件，包含轴、轴承座及密封",
                version="3.0",
                status="active",
                material_type_id=finish_type.id,
                weight_unit_id=kg_unit.id,
                origin_region_id=east_region.id,
                weight=8.5,
                drawing_number="ASSY-2023-001",
                supplier="自制"
            ),
        ]
        db.add_all(parts)
        db.commit()

        # 创建BOM关系
        p1 = db.query(Part).filter_by(part_code="P-001").first()
        p2 = db.query(Part).filter_by(part_code="P-002").first()
        p3 = db.query(Part).filter_by(part_code="P-003").first()
        p4 = db.query(Part).filter_by(part_code="P-004").first()
        p5 = db.query(Part).filter_by(part_code="P-005").first()

        boms = [
            BOM(parent_part_id=p5.id, child_part_id=p1.id, quantity=1.0, unit_id=pcs_unit.id, bom_level=1, notes="主传动轴 x1"),
            BOM(parent_part_id=p5.id, child_part_id=p2.id, quantity=2.0, unit_id=pcs_unit.id, bom_level=1, notes="两端各一个轴承座"),
            BOM(parent_part_id=p5.id, child_part_id=p3.id, quantity=4.0, unit_id=pcs_unit.id, bom_level=1, notes="每端两个深沟球轴承"),
            BOM(parent_part_id=p5.id, child_part_id=p4.id, quantity=4.0, unit_id=pcs_unit.id, bom_level=1, notes="每个轴承对应一个密封圈"),
        ]
        db.add_all(boms)
        db.commit()

        # 创建成本数据
        cost_items = [
            CostItem(
                part_id=p1.id, currency_id=cny.id,
                material_cost=380.0, manufacturing_cost=120.0, overhead_cost=60.0,
                total_cost=560.0, cost_version="v2.1",
                calculation_basis="材料：高强度钢5.2kg×73元/kg；制造：车削+磨削工时2h；间接：按制造成本50%"
            ),
            CostItem(
                part_id=p2.id, currency_id=cny.id,
                material_cost=85.0, manufacturing_cost=45.0, overhead_cost=22.5,
                total_cost=152.5, cost_version="v1.5",
                calculation_basis="材料：铸铁毛坯2.8kg×30元/kg；制造：铸造+加工工时1h；间接：按制造成本50%"
            ),
            CostItem(
                part_id=p3.id, currency_id=cny.id,
                material_cost=28.0, manufacturing_cost=0.0, overhead_cost=5.0,
                total_cost=33.0, cost_version="v1.0",
                calculation_basis="外购标准件SKF 6205，采购价28元；管理费用5元"
            ),
            CostItem(
                part_id=p4.id, currency_id=cny.id,
                material_cost=3.5, manufacturing_cost=0.0, overhead_cost=1.0,
                total_cost=4.5, cost_version="v1.2",
                calculation_basis="外购橡胶密封圈，采购价3.5元；管理费用1元"
            ),
            CostItem(
                part_id=p5.id, currency_id=cny.id,
                material_cost=748.0, manufacturing_cost=180.0, overhead_cost=150.0,
                total_cost=1078.0, cost_version="v3.0",
                calculation_basis="子件成本合计：P001×1+P002×2+P003×4+P004×4；装配工时3h；管理费用"
            ),
        ]
        db.add_all(cost_items)
        db.commit()

    except Exception:
        db.rollback()
    finally:
        db.close()
