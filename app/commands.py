from flask.cli import with_appcontext
from flask import current_app
import click

from app.extensions import db
from app.models import User, Permission, UserPermission

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

def populate_db_core():
    click.echo("Ensuring permission exists...")
    permission = Permission.query.filter_by(code="can_permissions").first()
    if not permission:
        permission = Permission(
            code="can_permissions",
            name="Permissions Management",
            description="Manage and assign permissions to any user.",
            is_active=True,
        )
        permission.create()
        click.echo("Created permission: can_permissions")
    elif not permission.is_active:
        permission.is_active = True
        permission.deactivated_at = None
        permission.deactivated_by_user_id = None
        permission.save()
        click.echo("Re-activated permission: can_permissions")

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

    click.echo("Ensuring user permission assignment exists...")
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
        click.echo("Assigned can_permissions to admin user.")
    else:
        click.echo("Permission already assigned to admin user.")

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