from sqlalchemy.future import select
from backend.app.database import AsyncSessionLocal
from backend.app.models.user import User, Role
from backend.app.models.warehouse import Warehouse, Zone, Location
from backend.app.models.product import Category, Product
from backend.app.models.inventory import Lot, Stock, StockMovement
from backend.app.core.security import get_password_hash
from datetime import datetime, timedelta
import uuid

async def seed_all():
    async with AsyncSessionLocal() as db:
        # 1. Seed Roles
        role_names = ["ADMIN", "SUPERVISOR", "OPERADOR", "VIEWER"]
        roles = {}
        
        for name in role_names:
            res = await db.execute(select(Role).filter(Role.name == name))
            db_role = res.scalars().first()
            if not db_role:
                db_role = Role(
                    name=name,
                    description=f"Rol de {name}",
                    permissions=["all"] if name == "ADMIN" else ["read", "write"]
                )
                db.add(db_role)
            roles[name] = db_role
            
        await db.flush()

        # 2. Seed Admin User
        admin_email = "admin@smartwms.com"
        res = await db.execute(select(User).filter(User.email == admin_email))
        db_admin = res.scalars().first()
        if not db_admin:
            db_admin = User(
                email=admin_email,
                hashed_password=get_password_hash("admin123"),
                full_name="Administrador Principal",
                is_active=True,
                is_superuser=True
            )
            db_admin.roles.append(roles["ADMIN"])
            db.add(db_admin)
            
        await db.flush()

        # 3. Seed Operator User
        operator_email = "operador@smartwms.com"
        res = await db.execute(select(User).filter(User.email == operator_email))
        db_operator = res.scalars().first()
        if not db_operator:
            db_operator = User(
                email=operator_email,
                hashed_password=get_password_hash("operador123"),
                full_name="Operador Bodega",
                is_active=True,
                is_superuser=False
            )
            db_operator.roles.append(roles["OPERADOR"])
            db.add(db_operator)
            
        await db.flush()

        # 4. Seed Warehouse
        res = await db.execute(select(Warehouse).filter(Warehouse.code == "B-CENTRAL"))
        db_wh = res.scalars().first()
        if not db_wh:
            db_wh = Warehouse(
                name="Bodega Central Santiago",
                code="B-CENTRAL",
                address="Av. Américo Vespucio 1500",
                city="Santiago",
                country="Chile",
                is_active=True
            )
            db.add(db_wh)
            await db.flush()
            
            # Seed Zones
            zones = {
                "REC": Zone(warehouse_id=db_wh.id, name="Zona Recepción", code="Z-REC", zone_type="RECEIVING"),
                "STO": Zone(warehouse_id=db_wh.id, name="Zona Almacenamiento Rack", code="Z-STO", zone_type="STORAGE"),
                "PIC": Zone(warehouse_id=db_wh.id, name="Zona de Picking", code="Z-PIC", zone_type="PICKING"),
                "DSP": Zone(warehouse_id=db_wh.id, name="Zona Despacho", code="Z-DSP", zone_type="DISPATCH")
            }
            for z in zones.values():
                db.add(z)
            await db.flush()
            
            # Seed Locations for each zone
            locations = []
            # Storage Rack locations: Aisle A, B, C | Rack 1, 2 | Level 1, 2 | Position 1, 2
            for aisle in ["A", "B"]:
                for rack in ["01", "02"]:
                    for level in ["01", "02"]:
                        for pos in ["01", "02"]:
                            code = f"LOC-{aisle}-{rack}-{level}-{pos}"
                            loc = Location(
                                zone_id=zones["STO"].id,
                                warehouse_id=db_wh.id,
                                code=code,
                                aisle=aisle,
                                rack=rack,
                                level=level,
                                position=pos,
                                max_weight=1500.0,
                                max_volume=12.0
                            )
                            db.add(loc)
                            locations.append(loc)
            
            # Dock/Receiving/Dispatch locations
            loc_rec = Location(zone_id=zones["REC"].id, warehouse_id=db_wh.id, code="LOC-RECEPCION-01", max_weight=5000.0, max_volume=50.0)
            loc_dsp = Location(zone_id=zones["DSP"].id, warehouse_id=db_wh.id, code="LOC-DESPACHO-01", max_weight=5000.0, max_volume=50.0)
            db.add(loc_rec)
            db.add(loc_dsp)
            locations.extend([loc_rec, loc_dsp])
            await db.flush()

            # 5. Seed Categories
            cats = {
                "ELE": Category(name="Electrónica", description="Equipos y repuestos electrónicos"),
                "ALI": Category(name="Alimentos", description="Alimentos perecibles y no perecibles"),
                "REP": Category(name="Repuestos", description="Repuestos mecánicos industriales")
            }
            for c in cats.values():
                db.add(c)
            await db.flush()

            # 6. Seed Products (15 Products)
            products_data = [
                # Electrónica
                ("PROD-LAP01", "Laptop Pro 15", "Laptop de alta gama para desarrollo", "ELE", "742839210923", "UNIDAD", 2.1, 0.005, 5, 50, 10),
                ("PROD-MOU02", "Mouse Óptico Inalámbrico", "Mouse ergonómico", "ELE", "742839210924", "UNIDAD", 0.1, 0.0005, 10, 100, 20),
                ("PROD-KEY03", "Teclado Mecánico RGB", "Teclado gaming switch azul", "ELE", "742839210925", "UNIDAD", 0.9, 0.002, 5, 50, 10),
                ("PROD-MON04", "Monitor UltraWide 34", "Monitor curvo 144Hz", "ELE", "742839210926", "UNIDAD", 8.5, 0.05, 2, 20, 5),
                ("PROD-HEA05", "Audífonos Bluetooth", "Audífonos con cancelación de ruido", "ELE", "742839210927", "UNIDAD", 0.3, 0.001, 10, 80, 15),
                # Alimentos
                ("PROD-CHO01", "Chocolate Bitter 70%", "Chocolate artesanal bitter", "ALI", "742839210928", "UNIDAD", 0.1, 0.0002, 50, 500, 100),
                ("PROD-GAL02", "Galletas de Avena pack", "Galletas saludables", "ALI", "742839210929", "UNIDAD", 0.25, 0.0008, 100, 1000, 200),
                ("PROD-CAF03", "Café de Grano Orgánico", "Café molido 500g", "ALI", "742839210930", "UNIDAD", 0.5, 0.0012, 30, 300, 60),
                ("PROD-TET04", "Té Verde Premium", "Caja 50 bolsitas de té verde", "ALI", "742839210931", "UNIDAD", 0.15, 0.0004, 40, 400, 80),
                ("PROD-ARR05", "Arroz Integral 1kg", "Arroz de grano largo integral", "ALI", "742839210932", "UNIDAD", 1.0, 0.0015, 200, 2000, 400),
                # Repuestos
                ("PROD-PER01", "Perno Hexagonal 3/8", "Perno de acero inoxidable", "REP", "742839210933", "UNIDAD", 0.05, 0.00005, 500, 10000, 1000),
                ("PROD-TUR02", "Tuerca de Seguridad 3/8", "Tuerca de acero con nylon", "REP", "742839210934", "UNIDAD", 0.02, 0.00002, 500, 10000, 1000),
                ("PROD-ROD03", "Rodamiento de Bolas 6204", "Rodamiento blindado industrial", "REP", "742839210935", "UNIDAD", 0.15, 0.0001, 50, 500, 100),
                ("PROD-COR04", "Correa de Transmisión V", "Correa de goma reforzada", "REP", "742839210936", "UNIDAD", 0.4, 0.0008, 20, 200, 40),
                ("PROD-FIL05", "Filtro de Aire Industrial", "Filtro de aire de alta eficiencia", "REP", "742839210937", "UNIDAD", 1.2, 0.004, 15, 150, 30)
            ]
            
            prods = {}
            for sku, name, desc, cat_code, bar, uom, w, v, min_s, max_s, reorder in products_data:
                db_prod = Product(
                    sku=sku,
                    name=name,
                    description=desc,
                    category_id=cats[cat_code].id,
                    barcode=bar,
                    unit_of_measure=uom,
                    weight=w,
                    volume=v,
                    min_stock=min_s,
                    max_stock=max_s,
                    reorder_point=reorder,
                    is_active=True
                )
                db.add(db_prod)
                prods[sku] = db_prod
            await db.flush()
            
            # Seed Lots for food products (lot numbers + expiry dates)
            exp_date_1 = datetime.utcnow() + timedelta(days=20)  # expiring soon!
            exp_date_2 = datetime.utcnow() + timedelta(days=120)
            
            lots = {
                "CHO-L01": Lot(product_id=prods["PROD-CHO01"].id, lot_number="LOT-CHO-001", manufacture_date=datetime.utcnow() - timedelta(days=10), expiry_date=exp_date_1, supplier="Proveedor Chocolates SA"),
                "CHO-L02": Lot(product_id=prods["PROD-CHO01"].id, lot_number="LOT-CHO-002", manufacture_date=datetime.utcnow(), expiry_date=exp_date_2, supplier="Proveedor Chocolates SA"),
                "GAL-L01": Lot(product_id=prods["PROD-GAL02"].id, lot_number="LOT-GAL-001", manufacture_date=datetime.utcnow() - timedelta(days=20), expiry_date=exp_date_2, supplier="Distribuidora Alimentos Ltda")
            }
            for l in lots.values():
                db.add(l)
            await db.flush()

            # 7. Seed Initial Stock & Stock Movements
            # Let's put Laptop in LOC-A-01-01-01
            s1 = Stock(product_id=prods["PROD-LAP01"].id, warehouse_id=db_wh.id, location_id=locations[0].id, quantity=15.0, reserved_quantity=0.0)
            locations[0].current_weight += prods["PROD-LAP01"].weight * 15
            locations[0].current_volume += prods["PROD-LAP01"].volume * 15
            db.add(s1)
            
            # Perno in LOC-B-01-01-01
            s2 = Stock(product_id=prods["PROD-PER01"].id, warehouse_id=db_wh.id, location_id=locations[8].id, quantity=1200.0, reserved_quantity=0.0)
            locations[8].current_weight += prods["PROD-PER01"].weight * 1200
            locations[8].current_volume += prods["PROD-PER01"].volume * 1200
            db.add(s2)
            
            # Chocolate expiring soon in LOC-A-01-01-02
            s3 = Stock(product_id=prods["PROD-CHO01"].id, warehouse_id=db_wh.id, location_id=locations[1].id, lot_id=lots["CHO-L01"].id, quantity=8.0, reserved_quantity=0.0)
            locations[1].current_weight += prods["PROD-CHO01"].weight * 8
            locations[1].current_volume += prods["PROD-CHO01"].volume * 8
            db.add(s3)
            
            # Chocolate fresh in LOC-A-01-01-02
            s4 = Stock(product_id=prods["PROD-CHO01"].id, warehouse_id=db_wh.id, location_id=locations[1].id, lot_id=lots["CHO-L02"].id, quantity=150.0, reserved_quantity=0.0)
            locations[1].current_weight += prods["PROD-CHO01"].weight * 150
            locations[1].current_volume += prods["PROD-CHO01"].volume * 150
            db.add(s4)
            
            # Audífonos (low stock) in LOC-A-01-02-01
            s5 = Stock(product_id=prods["PROD-HEA05"].id, warehouse_id=db_wh.id, location_id=locations[4].id, quantity=2.0, reserved_quantity=0.0)
            locations[4].current_weight += prods["PROD-HEA05"].weight * 2
            locations[4].current_volume += prods["PROD-HEA05"].volume * 2
            db.add(s5)
            
            await db.flush()
            
            # Seed Movements
            m1 = StockMovement(product_id=prods["PROD-LAP01"].id, warehouse_id=db_wh.id, to_location_id=locations[0].id, movement_type="ENTRY", quantity=15.0, reference_type="INITIAL", performed_by=db_admin.id, notes="Carga inicial de laptops")
            m2 = StockMovement(product_id=prods["PROD-PER01"].id, warehouse_id=db_wh.id, to_location_id=locations[8].id, movement_type="ENTRY", quantity=1200.0, reference_type="INITIAL", performed_by=db_admin.id, notes="Carga inicial de pernos")
            m3 = StockMovement(product_id=prods["PROD-CHO01"].id, warehouse_id=db_wh.id, to_location_id=locations[1].id, lot_id=lots["CHO-L01"].id, movement_type="ENTRY", quantity=8.0, reference_type="INITIAL", performed_by=db_admin.id, notes="Carga inicial chocolates lote 001")
            m4 = StockMovement(product_id=prods["PROD-CHO01"].id, warehouse_id=db_wh.id, to_location_id=locations[1].id, lot_id=lots["CHO-L02"].id, movement_type="ENTRY", quantity=150.0, reference_type="INITIAL", performed_by=db_admin.id, notes="Carga inicial chocolates lote 002")
            m5 = StockMovement(product_id=prods["PROD-HEA05"].id, warehouse_id=db_wh.id, to_location_id=locations[4].id, movement_type="ENTRY", quantity=2.0, reference_type="INITIAL", performed_by=db_admin.id, notes="Carga inicial audífonos")
            
            # Seed some past simulated exits for demand prediction modeling
            # Exit loop
            for d in range(1, 10):
                m_exit = StockMovement(
                    product_id=prods["PROD-CHO01"].id,
                    warehouse_id=db_wh.id,
                    from_location_id=locations[1].id,
                    lot_id=lots["CHO-L02"].id,
                    movement_type="EXIT",
                    quantity=3.0,
                    reference_type="ORDER",
                    performed_by=db_admin.id,
                    notes=f"Venta simulada día -{d}",
                    created_at=datetime.utcnow() - timedelta(days=d)
                )
                db.add(m_exit)
                
            db.add_all([m1, m2, m3, m4, m5])
            
        await db.commit()
