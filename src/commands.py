from flask.cli import with_appcontext
import click
from datetime import datetime

from src.extensions import db
from src.models import SeismicEvent, User, Role

# --- Core logic (გამოსაყენებელი როგორც CLI-დან, ისე ტესტებიდან) ---

def init_db_core():
    """Drop and recreate all database tables."""
    db.drop_all()
    db.create_all()

def populate_db_core():
    """Insert one sample seismic event (for manual testing/CLI)."""
    new_event = SeismicEvent(
        event_id=539870,
        seiscomp_oid="ies2024oeem",
        origin_time=datetime(2024, 6, 3, 22, 3, 40),
        origin_msec=130,
        latitude=42.5095,
        longitude=43.5328,
        depth=8,
        region_ge="ქალაქი ონი - სამხრეთ-აღმოსავლეთი - 8კმ. სოფელი ირი.",
        region_en="City Oni - South-East - 8km. Village Iri.",
        area="local",
        ml=5.33,
    )
    new_event.create()

    click.echo("Creating Role")
    role = Role(name="Admin", is_admin=True, can_users=True, can_shakemap=True)
    role.create()
    role = Role(name="User")
    role.create()

    click.echo("Creating Admin User")
    admin_user = User (
        name="Roma",
        lastname="Grigalashvili",
        email="roma.grigalashvili@iliauni.edu.ge",
        password="Grigalash1",
        role_id=1
    )
    admin_user.create()

# --- Click CLI commands (thin wrappers around core logic) ---

@click.command("init_db")
@with_appcontext
def init_db():
    """CLI: recreate DB schema."""
    click.echo("Creating Database")
    init_db_core()
    click.echo("Database Created")

@click.command("populate_db")
@with_appcontext
def populate_db():
    """CLI: populate DB with a single sample seismic event."""
    click.echo("Populating Database with sample seismic events...")
    populate_db_core()
    click.echo("Database Populated")