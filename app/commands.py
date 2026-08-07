from flask.cli import with_appcontext
from flask import current_app
import click

from datetime import datetime, timezone

from app.extensions import db
from app.models import (
    User,
    Permission,
    UserPermission,
    Magnitude,
    SeismicEvent,
    EventMagnitude,
)

# --- Core logic (გამოსაყენებელი როგორც CLI-დან, ისე ტესტებიდან) ---

def _is_production_environment():
    """ამოწმებს გაშვებულია თუ არა აპი production გარემოში."""
    config_flag = current_app.config.get("APP_ENV")
    return config_flag == "production"


def _require_reset_confirmation(confirm_text):
    """init_db-სთვის სავალდებულო დამცავი ტექსტის ვალიდაცია."""
    if confirm_text != "RESET_DB":
        raise click.ClickException( 
            "უსაფრთხოების მიზნით მიუთითე --confirm-text RESET_DB"
        )

def init_db_core():
    """Drop and recreate all database tables."""
    db.drop_all()
    db.create_all()

def _ensure_permission(code, name, description):
    """Create or re-activate a permission by code."""
    permission = Permission.query.filter_by(code=code).first()
    if not permission:
        permission = Permission(
            code=code,
            name=name,
            description=description,
            is_active=True,
        )
        permission.create()
        click.echo(f"Created permission: {code}")
    elif not permission.is_active:
        permission.is_active = True
        permission.deactivated_at = None
        permission.deactivated_by_user_id = None
        permission.save()
        click.echo(f"Re-activated permission: {code}")
    else:
        click.echo(f"Permission already exists: {code}")
    return permission


def _ensure_magnitude(code, description):
    """Create or update a magnitude catalog entry by code."""
    magnitude = Magnitude.query.filter_by(code=code).first()
    if not magnitude:
        magnitude = Magnitude(code=code, description=description)
        magnitude.create()
        click.echo(f"Created magnitude: {code}")
        return magnitude

    if magnitude.description != description:
        magnitude.description = description
        magnitude.save()
        click.echo(f"Updated magnitude description: {code}")
    else:
        click.echo(f"Magnitude already exists: {code}")
    return magnitude

def populate_db_core():
    click.echo("Ensuring permissions exist...")
    seed_permissions = [
        (
            "can_users",
            "Users Management",
            "Register and manage users.",
        ),
        (
            "can_permissions",
            "Permissions Management",
            "Manage and assign permissions to any user.",
        ),
        (
            "can_recips",
            "Recips Management",
            "Manage and assign recips to any user.",
        ),
        (
            "can_recips_read",
            "Recips Read-Only",
            "Read recipients list and details (for service API keys).",
        ),
        (
            "can_event_view",
            "Seismic Events View",
            "View seismic events, magnitudes, and beachballs.",
        ),
        (
            "can_event_edit",
            "Seismic Events Edit",
            "Create, update, and delete seismic events, magnitudes, and beachballs.",
        ),
    ]
    permissions = [
        _ensure_permission(code, name, description)
        for code, name, description in seed_permissions
    ]

    click.echo("Ensuring magnitude catalog exists...")
    seed_magnitudes = [
        (
            "ML",
            "Local Magnitude – Used for nearby earthquakes; the traditional Richter-scale magnitude.",
        ),
        (
            "MB",
            "Body-wave Magnitude – Calculated from the amplitude of body (P) waves.",
        ),
        (
            "MS",
            "Surface-wave Magnitude – Calculated from the amplitude of long-period surface waves.",
        ),
        (
            "MD",
            "Duration Magnitude – Estimated from the duration of the recorded seismic signal.",
        ),
        (
            "MW",
            "Moment Magnitude – Calculated from the seismic moment; the modern standard for measuring earthquake size.",
        ),
        (
            "K",
            "Energy Class – Logarithmic measure of earthquake energy, used mainly in former Soviet and Eastern European seismic networks.",
        ),
        (
            "MPV",
            "Peak Velocity Magnitude – Magnitude estimated from peak ground velocity measurements.",
        ),
        (
            "MLH",
            "Horizontal Local Magnitude – Local magnitude calculated using the horizontal components of seismic recordings.",
        ),
        (
            "MC",
            "Coda Magnitude – Magnitude calculated from the duration of the seismic coda (the tail of the seismic signal).",
        ),
        (
            "MLV",
            "Vertical Local Magnitude – Local magnitude calculated using the vertical component of seismic recordings.",
        ),
        (
            "M",
            "Generic Magnitude – Generic magnitude designation used when the specific magnitude scale is unknown or unspecified.",
        ),
    ]
    for code, description in seed_magnitudes:
        _ensure_magnitude(code, description)

    click.echo("Ensuring admin user exists...")
    admin_email = "roma.grigalashvili@iliauni.edu.ge"
    admin_user = User.query.filter_by(email=admin_email).first()
    if not admin_user:
        admin_user = User(
            first_name="Roma",
            last_name="Grigalashvili",
            email=admin_email,
            is_active=True,
        )
        admin_user.password = "PASSWORD"
        admin_user.create()
        click.echo(f"Created user: {admin_email}")
    else:
        click.echo(f"User already exists: {admin_email}")

    click.echo("Ensuring user permission assignments exist...")
    for permission in permissions:
        assignment = UserPermission.query.filter_by(
            user_id=admin_user.id,
            permission_id=permission.id,
            degranted_at=None,
        ).first()

        if not assignment:
            assignment = UserPermission(
                user_id=admin_user.id,
                permission_id=permission.id,
                granted_by_user_id=admin_user.id,
            )
            assignment.create()
            click.echo(f"Assigned {permission.code} to admin user.")
        else:
            click.echo(f"Permission already assigned to admin user: {permission.code}")

    click.echo("Ensuring sample seismic event exists...")
    sample_oid = "Origin/TEST.20260806.120000.01"
    sample_event = SeismicEvent.query.filter_by(seiscomp_oid=sample_oid).first()
    if not sample_event:
        sample_event = SeismicEvent(
            iesdata_id="IES-TEST-0001",
            seiscomp_oid=sample_oid,
            origin_time=datetime(2026, 8, 6, 12, 0, 0, tzinfo=timezone.utc),
            latitude=41.7151,
            longitude=44.8271,
            depth=10.5,
            location_ge="თბილისის მახლობლად",
            location_en="Near Tbilisi",
            area="Georgia",
            is_automatic=False,
        )
        sample_event.create()
        click.echo(f"Created sample seismic event: {sample_oid}")
    else:
        click.echo(f"Sample seismic event already exists: {sample_oid}")

    ml_magnitude = Magnitude.query.filter_by(code="ML").first()
    if ml_magnitude and sample_event:
        existing_ml = EventMagnitude.query.filter_by(
            event_id=sample_event.id,
            magnitude_id=ml_magnitude.id,
        ).first()
        if not existing_ml:
            EventMagnitude(
                event_id=sample_event.id,
                magnitude_id=ml_magnitude.id,
                value=3.4,
            ).create()
            click.echo("Assigned sample ML magnitude 3.4 to test event.")
        else:
            click.echo("Sample ML magnitude already assigned to test event.")

    User.save()


# --- Click CLI commands (thin wrappers around core logic) ---

@click.command("init_db")
@click.option(
    "--force",
    is_flag=True,
    help="Production გარემოში აუცილებელია ამ flag-ის გადაცემა.",
)
@click.option(
    "--confirm-text",
    default="",
    help='უსაფრთხოებისთვის ზუსტად მიუთითე: RESET_DB',
)
@with_appcontext
def init_db(force, confirm_text):
    """CLI: recreate DB schema."""
    if _is_production_environment() and not force:
        raise click.ClickException(
            "Production გარემოში init_db დაბლოკილია. გამოიყენე --force."
        )

    _require_reset_confirmation(confirm_text)

    if not force and not click.confirm("ნამდვილად გსურს ბაზის სრული reset (drop/create)?"):
        click.echo("ოპერაცია გაუქმდა.")
        return

    click.echo("Creating Database")
    init_db_core()
    click.echo("Database Created")

@click.command("populate_db")
@click.option(
    "--force",
    is_flag=True,
    help="Production გარემოში აუცილებელია ამ flag-ის გადაცემა.",
)
@with_appcontext
def populate_db(force):
    """CLI: populate DB with a single sample seismic event."""
    if _is_production_environment() and not force:
        raise click.ClickException(
            "Production გარემოში populate_db დაბლოკილია. გამოიყენე --force."
        )

    click.echo("Populating Database with sample seismic events...")
    populate_db_core()
    click.echo("Database Populated")