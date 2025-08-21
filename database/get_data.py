#!/usr/bin/env python3
"""
Enhanced Database Inspector for Mental Health Platform
=====================================================

Comprehensive database inspection tool that safely discovers and displays
all tables, schemas, and data from a SQLAlchemy-based database.
Specifically designed for the Mental Health Platform using the models package.

Features:
- Auto-discovery of all Mental Health Platform models
- Safe error handling with multiple fallback strategies
- Formatted output with proper data type handling
- Schema information display with relationship mapping
- Sample data creation using platform-specific models
- Clinical data analysis and reporting
- Patient/Specialist/Admin data management
- Configurable data preview limits
- Summary and detailed views
"""

import inspect
import sys
from typing import List, Dict, Any, Optional, Tuple, Type, Union
from sqlalchemy import text, MetaData, Table, inspect as sqlalchemy_inspect
from sqlalchemy.orm import Session, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.relationships import RelationshipProperty
from database import SessionLocal, Base, engine
from datetime import datetime, timedelta
import json
import traceback
from dataclasses import dataclass
import random
from faker import Faker
from models import EmailVerificationStatus

# Import all models from the mental health platform 
try:
    from models import *
    MODELS_IMPORTED = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import models: {e}")
    MODELS_IMPORTED = False

fake = Faker()

@dataclass
class TableInfo:
    """Container for table information with enhanced metadata"""
    name: str
    model_class: Optional[Type] = None
    row_count: int = 0
    columns: List[Tuple[str, str, bool]] = None
    relationships: List[Tuple[str, str, str]] = None
    has_model: bool = False
    is_junction_table: bool = False
    primary_keys: List[str] = None
    foreign_keys: List[Tuple[str, str]] = None
    
    def __post_init__(self):
        if self.columns is None:
            self.columns = []
        if self.relationships is None:
            self.relationships = []
        if self.primary_keys is None:
            self.primary_keys = []
        if self.foreign_keys is None:
            self.foreign_keys = []


class MentalHealthDatabaseInspector:
    """Enhanced database inspector specifically designed for Mental Health Platform"""
    
    def __init__(self, session_factory=SessionLocal, base_class=Base, db_engine=engine):
        self.session_factory = session_factory
        self.base_class = base_class
        self.engine = db_engine
        self.max_preview_rows = 5
        self.max_string_length = 100
        
        # Platform-specific model categories
        self.model_categories = {
            'Core Models': ['Patient', 'Specialist', 'Admin'],
            'Appointment System': ['Appointment', 'AppointmentReminder', 'AppointmentDocument'],
            'Clinical Records': ['DiagnosisRecord', 'SymptomRecord', 'TreatmentRecord'],
            'Feedback System': ['Feedback', 'FeedbackFollowUp', 'AgentLog', 'AuditLog'],
            'Licensing': ['SpecialistLicense'],
            'Support': ['EmergencyContact']
        }
        
    def get_platform_models(self) -> Dict[str, List[Type]]:
        """Get all Mental Health Platform models organized by category"""
        if not MODELS_IMPORTED:
            return {}
            
        model_dict = {}
        
        # Get all model classes from the Base registry
        all_models = []
        try:
            for mapper in self.base_class.registry.mappers:
                model_class = mapper.class_
                if hasattr(model_class, '__tablename__'):
                    all_models.append(model_class)
        except Exception as e:
            print(f"⚠️  Could not get models from Base registry: {e}")
            return {}
        
        # Categorize models
        for category, model_names in self.model_categories.items():
            category_models = []
            for model in all_models:
                if model.__name__ in model_names:
                    category_models.append(model)
            if category_models:
                model_dict[category] = category_models
        
        # Add any uncategorized models
        categorized_names = set()
        for models in model_dict.values():
            categorized_names.update(model.__name__ for model in models)
        
        uncategorized = [model for model in all_models 
                        if model.__name__ not in categorized_names]
        if uncategorized:
            model_dict['Other Models'] = uncategorized
            
        return model_dict
    
    def analyze_model_relationships(self, model_class: Type) -> List[Tuple[str, str, str]]:
        """Analyze relationships for a given model"""
        relationships = []
        
        try:
            # Get all relationship properties
            for attr_name in dir(model_class):
                try:
                    attr = getattr(model_class, attr_name)
                    if hasattr(attr, 'property') and isinstance(attr.property, RelationshipProperty):
                        rel_prop = attr.property
                        target_class = rel_prop.mapper.class_.__name__
                        
                        # Determine relationship type
                        if rel_prop.uselist:
                            rel_type = "One-to-Many" if not rel_prop.back_populates else "Many-to-Many"
                        else:
                            rel_type = "Many-to-One"
                        
                        relationships.append((attr_name, target_class, rel_type))
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"⚠️  Error analyzing relationships for {model_class.__name__}: {e}")
            
        return relationships
    
    def get_model_constraints(self, model_class: Type) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Get primary keys and foreign keys for a model"""
        primary_keys = []
        foreign_keys = []
        
        try:
            table = model_class.__table__
            
            # Get primary keys
            primary_keys = [col.name for col in table.primary_key.columns]
            
            # Get foreign keys
            for constraint in table.foreign_keys:
                foreign_keys.append((constraint.parent.name, str(constraint.column)))
                
        except Exception as e:
            print(f"⚠️  Error getting constraints for {model_class.__name__}: {e}")
            
        return primary_keys, foreign_keys
    
    def get_table_schema_enhanced(self, db: Session, table_name: str, model_class: Type = None) -> List[Tuple[str, str, bool]]:
        """Get enhanced column information for a table"""
        if model_class:
            try:
                columns = []
                for col in model_class.__table__.columns:
                    col_type = str(col.type)
                    # Add enum values if it's an enum column
                    if hasattr(col.type, 'enums') and col.type.enums:
                        col_type += f" {list(col.type.enums)}"
                    columns.append((col.name, col_type, col.nullable))
                return columns
            except Exception as e:
                print(f"⚠️  Error getting enhanced schema for {table_name}: {e}")
        
        # Fallback to basic schema
        return self.get_table_schema(db, table_name)
    
    def get_table_schema(self, db: Session, table_name: str) -> List[Tuple[str, str, bool]]:
        """Get basic column information for a table"""
        # Try information_schema first
        try:
            result = db.execute(text(f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
                ORDER BY ordinal_position
            """))
            columns = result.fetchall()
            if columns:
                return [(col[0], col[1], col[2] in ('YES', 'Y', '1', True)) for col in columns]
        except Exception:
            pass
        
        # Fallback to SQLAlchemy metadata
        try:
            table = self.base_class.metadata.tables.get(table_name)
            if table is not None:
                return [(col.name, str(col.type), col.nullable) for col in table.columns]
        except Exception:
            pass
        
        return []
    
    def get_table_row_count(self, db: Session, table_name: str) -> int:
        """Get the number of rows in a table"""
        try:
            result = db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar() or 0
        except Exception:
            return 0
    
    def collect_enhanced_table_info(self, db: Session) -> List[TableInfo]:
        """Collect comprehensive information about all tables with platform-specific enhancements"""
        tables_info = []
        
        # Get platform models organized by category
        model_categories = self.get_platform_models()
        all_models = []
        for models in model_categories.values():
            all_models.extend(models)
        
        model_tables = {model.__tablename__: model for model in all_models}
        
        # Get all database tables
        db_tables = self.get_database_tables(db)
        
        # Process all tables
        all_tables = set(db_tables + list(model_tables.keys()))
        
        for table_name in all_tables:
            try:
                model_class = model_tables.get(table_name)
                relationships = self.analyze_model_relationships(model_class) if model_class else []
                primary_keys, foreign_keys = self.get_model_constraints(model_class) if model_class else ([], [])
                
                info = TableInfo(
                    name=table_name,
                    model_class=model_class,
                    has_model=table_name in model_tables,
                    row_count=self.get_table_row_count(db, table_name),
                    columns=self.get_table_schema_enhanced(db, table_name, model_class),
                    relationships=relationships,
                    primary_keys=primary_keys,
                    foreign_keys=foreign_keys,
                    is_junction_table=len(primary_keys) > 1 and len(foreign_keys) > 1
                )
                tables_info.append(info)
            except Exception as e:
                print(f"⚠️  Error collecting info for table {table_name}: {e}")
                tables_info.append(TableInfo(name=table_name))
        
        return sorted(tables_info, key=lambda x: x.name)
    
    def get_database_tables(self, db: Session) -> List[str]:
        """Get all table names directly from the database"""
        queries = [
            "SELECT tablename FROM pg_tables WHERE schemaname = 'public'",
            "SELECT table_name FROM information_schema.tables WHERE table_schema = DATABASE()",
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'",
            "SELECT table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE'",
        ]
        
        for query in queries:
            try:
                result = db.execute(text(query))
                tables = [row[0] for row in result.fetchall()]
                if tables:
                    return tables
            except Exception:
                continue
        
        # Fallback to SQLAlchemy metadata reflection
        try:
            metadata = MetaData()
            metadata.reflect(bind=self.engine)
            return list(metadata.tables.keys())
        except Exception as e:
            print(f"⚠️  Could not reflect database metadata: {e}")
            return []
    
    def format_value(self, value: Any) -> str:
        """Format values for better display with platform-specific handling"""
        if value is None:
            return "NULL"
        elif isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, (dict, list)):
            try:
                return json.dumps(value, indent=2, default=str)
            except:
                return str(value)
        elif isinstance(value, str):
            if len(value) > self.max_string_length:
                return f"{value[:self.max_string_length]}..."
            return value
        else:
            return str(value)
    
    def print_enhanced_table_schema(self, table_info: TableInfo):
        """Print enhanced table schema with relationships and constraints"""
        if not table_info.columns:
            print("   📋 Schema: <unable to determine>")
            return
        
        print("   📋 Schema:")
        for col_name, col_type, nullable in table_info.columns:
            null_info = "NULL" if nullable else "NOT NULL"
            pk_info = " [PK]" if col_name in table_info.primary_keys else ""
            fk_info = ""
            for fk_col, fk_ref in table_info.foreign_keys:
                if fk_col == col_name:
                    fk_info = f" [FK -> {fk_ref}]"
                    break
            
            print(f"      • {col_name}: {col_type} ({null_info}){pk_info}{fk_info}")
        
        # Print relationships
        if table_info.relationships:
            print("   🔗 Relationships:")
            for rel_name, target_class, rel_type in table_info.relationships:
                print(f"      • {rel_name} -> {target_class} ({rel_type})")
        
        print()
    
    def print_table_data_enhanced(self, db: Session, table_info: TableInfo):
        """Print formatted table data with enhanced platform-specific formatting"""
        if table_info.row_count == 0:
            print("   📊 Data: (No data found)")
            return
        
        print(f"   📊 Data preview (showing up to {self.max_preview_rows} rows):")
        
        try:
            if table_info.model_class:
                # Use SQLAlchemy model
                rows = db.query(table_info.model_class).limit(self.max_preview_rows).all()
                
                for i, row in enumerate(rows, 1):
                    print(f"\n   ┌─── Row {i} ───────────────────────────────────────")
                    
                    # Show primary key fields first
                    for pk_col in table_info.primary_keys:
                        try:
                            value = getattr(row, pk_col)
                            formatted_value = self.format_value(value)
                            print(f"   │ {pk_col:20} : {formatted_value} [PRIMARY KEY]")
                        except AttributeError:
                            pass
                    
                    # Show other fields
                    for column in table_info.model_class.__table__.columns:
                        if column.name not in table_info.primary_keys:
                            try:
                                value = getattr(row, column.name)
                                formatted_value = self.format_value(value)
                                print(f"   │ {column.name:20} : {formatted_value}")
                            except AttributeError:
                                print(f"   │ {column.name:20} : <unable to read>")
                    
                    print(f"   └─────────────────────────────────────────────────")
            else:
                # Use raw SQL
                result = db.execute(text(f"SELECT * FROM {table_info.name} LIMIT {self.max_preview_rows}"))
                rows = result.fetchall()
                
                if rows:
                    columns = result.keys()
                    
                    for i, row in enumerate(rows, 1):
                        print(f"\n   ┌─── Row {i} ───────────────────────────────────────")
                        row_dict = dict(row._mapping)
                        
                        for col_name in columns:
                            value = row_dict.get(col_name)
                            formatted_value = self.format_value(value)
                            print(f"   │ {col_name:20} : {formatted_value}")
                        
                        print(f"   └─────────────────────────────────────────────────")
            
            if table_info.row_count > self.max_preview_rows:
                print(f"\n   ... and {table_info.row_count - self.max_preview_rows} more rows")
                
        except Exception as e:
            print(f"   ❌ Error reading data: {str(e)}")
    
    def print_platform_summary(self):
        """Print Mental Health Platform specific database summary"""
        db: Session = self.session_factory()
        try:
            print("🏥 MENTAL HEALTH PLATFORM DATABASE SUMMARY")
            print("=" * 50)
            
            tables_info = self.collect_enhanced_table_info(db)
            model_categories = self.get_platform_models()
            
            # Overall stats
            total_tables = len(tables_info)
            total_rows = sum(t.row_count for t in tables_info)
            model_count = sum(1 for t in tables_info if t.has_model)
            
            print(f"📊 Total tables: {total_tables}")
            print(f"📦 SQLAlchemy models: {model_count}")
            print(f"📈 Total records: {total_rows}")
            print()
            
            # Category-wise breakdown
            print("📋 Model Categories:")
            for category, models in model_categories.items():
                print(f"\n   🏷️  {category}:")
                for model in models:
                    table_info = next((t for t in tables_info if t.name == model.__tablename__), None)
                    if table_info:
                        print(f"      • {model.__name__} ({model.__tablename__}): {table_info.row_count} records")
                    else:
                        print(f"      • {model.__name__} ({model.__tablename__}): <not found>")
            
            # Quick stats for key entities
            print("\n📊 Key Entity Counts:")
            key_entities = ['Patient', 'Specialist', 'Admin', 'Appointment', 'Feedback']
            for entity in key_entities:
                table_info = next((t for t in tables_info if t.model_class and t.model_class.__name__ == entity), None)
                if table_info:
                    print(f"   • {entity}s: {table_info.row_count}")
            
        except Exception as e:
            print(f"❌ Error generating platform summary: {e}")
            traceback.print_exc()
        finally:
            db.close()
    
    def print_detailed_platform_report(self):
        """Print comprehensive Mental Health Platform database report"""
        db: Session = self.session_factory()
        print("🚀 MENTAL HEALTH PLATFORM - COMPREHENSIVE DATABASE INSPECTION")
        print("=" * 70)
        
        try:
            tables_info = self.collect_enhanced_table_info(db)
            model_categories = self.get_platform_models()
            
            print(f"📊 Database contains {len(tables_info)} tables")
            print(f"📦 {sum(1 for t in tables_info if t.has_model)} tables have corresponding models")
            print("=" * 70)
            
            # Report by category
            for category, models in model_categories.items():
                print(f"\n🏷️  {category.upper()}")
                print("-" * 50)
                
                for model in models:
                    table_info = next((t for t in tables_info if t.name == model.__tablename__), None)
                    if table_info:
                        print(f"\n📋 TABLE: {table_info.name.upper()}")
                        print(f"📦 Model: {model.__name__}")
                        print(f"📈 Records: {table_info.row_count}")
                        print(f"🔧 Junction Table: {'Yes' if table_info.is_junction_table else 'No'}")
                        
                        # Enhanced schema display
                        self.print_enhanced_table_schema(table_info)
                        
                        # Data preview
                        self.print_table_data_enhanced(db, table_info)
                        
                        print("-" * 50)
            
            # Show any uncategorized tables
            uncategorized = [t for t in tables_info if not t.has_model or 
                           (t.model_class and t.model_class.__name__ not in 
                            [m.__name__ for models in model_categories.values() for m in models])]
            
            if uncategorized:
                print(f"\n🏷️  UNCATEGORIZED TABLES")
                print("-" * 50)
                for table_info in uncategorized:
                    print(f"\n📋 TABLE: {table_info.name.upper()}")
                    if table_info.has_model:
                        print(f"📦 Model: {table_info.model_class.__name__}")
                    else:
                        print("📋 No SQLAlchemy model")
                    print(f"📈 Records: {table_info.row_count}")
                    
                    self.print_enhanced_table_schema(table_info)
                    self.print_table_data_enhanced(db, table_info)
                    print("-" * 50)
            
        except Exception as e:
            print(f"❌ Critical error during platform inspection: {str(e)}")
            traceback.print_exc()
        finally:
            db.close()
            print("\n" + "=" * 70)
            print("✅ Mental Health Platform database inspection completed!")
    
    def create_sample_platform_data(self):
        """Create sample data specific to Mental Health Platform"""
        if not MODELS_IMPORTED:
            print("❌ Models not imported - cannot create sample data")
            return
        
        db: Session = self.session_factory()
        try:
            print("🌱 Creating Mental Health Platform sample data...")
            
            # Create sample patients
            patients = []
            for i in range(3):
                patient = Patient(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email(),
                    phone=fake.phone_number()[:15],
                    date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=80),
                    gender=random.choice(list(GenderEnum)),
                    address=fake.address()[:200],
                    city=fake.city(),
                    emergency_contact_name=fake.name(),
                    emergency_contact_phone=fake.phone_number()[:15],
                    preferred_language=random.choice(list(LanguageEnum)),
                    consultation_mode=random.choice(list(ConsultationModeEnum)),
                    mental_health_history=fake.text(max_nb_chars=500),
                    current_medications=fake.text(max_nb_chars=200),
                    distress_level=random.choice(list(SeverityEnum)),
                    risk_level=random.choice(list(SeverityEnum)),
                    created_at=fake.date_time_this_year(),
                    updated_at=fake.date_time_this_month()
                )
                db.add(patient)
                patients.append(patient)
            
            # Create sample specialists
            specialists = []
            for i in range(2):
                specialist = Specialist(
                    first_name=fake.first_name(),
                    last_name=fake.last_name(),
                    email=fake.email(),
                    phone=fake.phone_number()[:15],
                    specialist_type=random.choice(list(SpecialistType)),
                    specialization=random.choice(list(Specialization)),
                    years_of_experience=random.randint(1, 30),
                    consultation_fee=random.randint(1000, 5000),
                    bio=fake.text(max_nb_chars=500),
                    city=fake.city(),
                    availability_status=AvailabilityStatus.AVAILABLE,
                    verification_status=EmailVerificationStatus.VERIFIED,
                    rating=round(random.uniform(3.5, 5.0), 1),
                    created_at=fake.date_time_this_year(),
                    updated_at=fake.date_time_this_month()
                )
                db.add(specialist)
                specialists.append(specialist)
            
            # Create sample admin
            admin = Admin(
                first_name=fake.first_name(),
                last_name=fake.last_name(),
                email=fake.email(),
                phone=fake.phone_number()[:15],
                employee_id=f"EMP{random.randint(1000, 9999)}",
                role=random.choice(list(AdminRoleEnum)),
                status=AdminStatusEnum.ACTIVE,
                created_at=fake.date_time_this_year(),
                updated_at=fake.date_time_this_month()
            )
            db.add(admin)
            
            db.commit()
            
            # Create appointments
            for i in range(5):
                appointment = Appointment(
                    patient_id=random.choice(patients).id,
                    specialist_id=random.choice(specialists).id,
                    appointment_date=fake.date_time_between(start_date='+1d', end_date='+30d'),
                    appointment_type=random.choice(list(AppointmentTypeEnum)),
                    status=random.choice(list(AppointmentStatusEnum)),
                    notes=fake.text(max_nb_chars=200),
                    fee=random.randint(1000, 5000),
                    payment_status=random.choice(list(PaymentStatusEnum)),
                    created_at=fake.date_time_this_month(),
                    updated_at=fake.date_time_this_week()
                )
                db.add(appointment)
            
            # Create feedback
            for i in range(3):
                feedback = Feedback(
                    user_id=random.choice(patients).id,
                    user_type=UserTypeEnum.PATIENT,
                    feedback_type=random.choice(list(FeedbackTypeEnum)),
                    subject=fake.sentence(nb_words=6),
                    message=fake.text(max_nb_chars=300),
                    rating=random.randint(1, 5),
                    status=random.choice(list(FeedbackStatusEnum)),
                    created_at=fake.date_time_this_month(),
                    updated_at=fake.date_time_this_week()
                )
                db.add(feedback)
            
            db.commit()
            
            print("✅ Sample Mental Health Platform data created successfully!")
            print(f"   • {len(patients)} patients")
            print(f"   • {len(specialists)} specialists")  
            print(f"   • 1 admin")
            print(f"   • 5 appointments")
            print(f"   • 3 feedback entries")
            
        except Exception as e:
            print(f"❌ Error creating sample data: {e}")
            traceback.print_exc()
            db.rollback()
        finally:
            db.close()
    
    def analyze_platform_relationships(self):
        """Analyze and display Mental Health Platform model relationships"""
        if not MODELS_IMPORTED:
            print("❌ Models not imported - cannot analyze relationships")
            return
        
        print("🔗 MENTAL HEALTH PLATFORM - MODEL RELATIONSHIPS")
        print("=" * 60)
        
        model_categories = self.get_platform_models()
        
        for category, models in model_categories.items():
            print(f"\n🏷️  {category}:")
            
            for model in models:
                relationships = self.analyze_model_relationships(model)
                if relationships:
                    print(f"\n   📦 {model.__name__}:")
                    for rel_name, target_class, rel_type in relationships:
                        print(f"      • {rel_name} -> {target_class} ({rel_type})")
                else:
                    print(f"\n   📦 {model.__name__}: No relationships")
    
    def ensure_tables_exist(self):
        """Ensure all Mental Health Platform tables are created"""
        try:
            self.base_class.metadata.create_all(bind=self.engine)
            print("✅ Mental Health Platform database tables verified/created")
        except Exception as e:
            print(f"⚠️  Warning during table creation: {e}")
    
    def drop_all_data(self, confirm: bool = False):
        """Drop all data from all tables (keeps table structure)"""
        if not confirm:
            print("⚠️  This will DELETE ALL DATA from all Mental Health Platform tables!")
            response = input("Are you sure you want to continue? (type 'YES' to confirm): ")
            if response != 'YES':
                print("❌ Operation cancelled")
                return False
        
        db: Session = self.session_factory()
        try:
            print("🗑️  Dropping all Mental Health Platform data...")
            
            tables_info = self.collect_enhanced_table_info(db)
            
            # Disable foreign key constraints
            try:
                db.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
            except:
                try:
                    db.execute(text("PRAGMA foreign_keys = OFF"))
                except:
                    try:
                        db.execute(text("SET session_replication_role = 'replica'"))
                    except:
                        pass
            
            deleted_count = 0
            for table_info in tables_info:
                try:
                    if table_info.row_count > 0:
                        result = db.execute(text(f"DELETE FROM {table_info.name}"))
                        deleted_rows = result.rowcount if hasattr(result, 'rowcount') else 0
                        deleted_count += deleted_rows
                        print(f"   🗑️  Cleared {table_info.name}: {deleted_rows} rows deleted")
                except Exception as e:
                    print(f"   ❌ Error clearing {table_info.name}: {e}")
            
            # Re-enable foreign key constraints
            try:
                db.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
            except:
                try:
                    db.execute(text("PRAGMA foreign_keys = ON"))
                except:
                    try:
                        db.execute(text("SET session_replication_role = 'origin'"))
                    except:
                        pass
            
            db.commit()
            print(f"✅ Successfully deleted {deleted_count} rows from Mental Health Platform")
            return True
            
        except Exception as e:
            print(f"❌ Error during data deletion: {e}")
            db.rollback()
            return False
        finally:
            db.close()
    
def drop_tables(table_names):
    """Drop specified tables from the database."""
    with engine.connect() as conn:
        for table in table_names:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                print(f"Dropped table: {table}")
            except Exception as e:
                print(f"Error dropping table {table}: {e}")


def display_platform_menu():
    """Display the Mental Health Platform specific menu"""
    print("\n" + "=" * 70)
    print("🏥 MENTAL HEALTH PLATFORM - DATABASE ")
    print("INSPECTION AND MANAGEMENT MENU")
    print("=" * 70)
    print("1. View Mental Health Platform Database Summary")
    print("2. View Detailed Mental Health Platform Database Report")
    print("3. Create Sample Mental Health Platform Data")
    print("4. Analyze Mental Health Platform Model Relationships")
    print("5. Ensure Mental Health Platform Tables Exist")
    print("6. Drop All Mental Health Platform Data")
    print("0. Exit")
    print("=" * 70)
    
def main():
    """Main entry point for Mental Health Platform database inspection"""
    inspector = MentalHealthDatabaseInspector()
    
    while True:
        display_platform_menu()
        choice = input("Select an option: ")
        try:
            if choice == '1':
                inspector.print_platform_summary()
            elif choice == '2':
                inspector.print_detailed_platform_report()
            elif choice == '3':
                inspector.create_sample_platform_data()
            elif choice == '4':
                inspector.analyze_platform_relationships()
            elif choice == '5':
                inspector.ensure_tables_exist()
            elif choice == '6':
                if inspector.drop_all_data(confirm=True):
                    print("All data has been successfully deleted.")
            elif choice == '0':
                print("Exiting Mental Health Platform database inspection.")
                break
            else:
                print("Invalid option. Please try again.")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            traceback.print_exc()
        finally:
            print("\n" + "=" * 70)
            print("Returning to Mental Health Platform menu...\n")
            
            
def run_platform_inspection():
    """Run the Mental Health Platform database inspection"""
    try:
        main()
    except Exception as e:
        print(f"❌ Critical error during Mental Health Platform inspection: {e}")
        traceback.print_exc()
    finally:
        print("Thank you for using the Mental Health Platform database inspection tool!")
        print("Goodbye! 👋")
        
if __name__ == "__main__":
    run_platform_inspection()
