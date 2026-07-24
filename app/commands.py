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

def _ensure_schema_exists():
    """Fail fast if tables were never created (run init_db first)."""
    required_tables = {"users", "permissions", "user_permissions"}
    existing = set(db.inspect(db.engine).get_table_names())
    missing = required_tables - existing
    if missing:
        raise click.ClickException(
            f"Missing tables: {', '.join(sorted(missing))}. "
            "Run: flask init_db --confirm-text RESET_DB"
        )


def _ensure_permission(code, name, description):
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
        return permission

    if not permission.is_active:
        permission.is_active = True
        permission.deactivated_at = None
        permission.deactivated_by_user_id = None
        permission.save()
        click.echo(f"Re-activated permission: {code}")
    else:
        click.echo(f"Permission already exists: {code}")
    return permission


def _ensure_assignment(user, permission):
    assignment = (
        UserPermission.query.filter_by(
            user_id=user.id,
            permission_id=permission.id,
        )
        .filter(UserPermission.degranted_at.is_(None))
        .first()
    )
    if assignment:
        click.echo(f"Permission already assigned: {permission.code}")
        return assignment

    assignment = UserPermission(
        user_id=user.id,
        permission_id=permission.id,
        granted_by_user_id=user.id,
    )
    assignment.create()
    click.echo(f"Assigned {permission.code} to admin user.")
    return assignment


def populate_db_core():
    _ensure_schema_exists()

    click.echo("Ensuring permissions exist...")
    can_permissions = _ensure_permission(
        code="can_permissions",
        name="Permissions Management",
        description="Manage and assign permissions to any user.",
    )
    can_users = _ensure_permission(
        code="can_users",
        name="Users Management",
        description="Manage user accounts and registration.",
    )

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
        # Seed password bypasses API policy; change after first login in real envs.
        admin_user.password = "AdminPass1!"
        admin_user.create()
        click.echo(f"Created user: {admin_email}")
    else:
        click.echo(f"User already exists: {admin_email}")

    click.echo("Ensuring user permission assignments exist...")
    _ensure_assignment(admin_user, can_permissions)
    _ensure_assignment(admin_user, can_users)


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
    """CLI: seed admin user and baseline permissions."""
    if _is_production_environment() and not force:
        raise click.ClickException(
            "Production გარემოში populate_db დაბლოკილია. გამოიყენე --force."
        )

    click.echo("Populating Database...")
    populate_db_core()
    click.echo("Database Populated")