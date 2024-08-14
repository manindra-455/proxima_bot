import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, TextInput, Modal
from discord import Permissions, PermissionOverwrite
import random
import string
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
APIBOT = os.getenv("DISCORD_TOKEN")


intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True
intents.messages = True

client = commands.Bot(command_prefix='!', intents=intents)

# File paths for storing data
TOURNAMENTS_FILE = "tournaments.json"
REGISTRATION_SETTINGS_FILE = "registration_settings.json"
SS_VERIFY_FILES_FILE = "ss_verify_files.json"
SCRIMS_REG_SETTINGS_FILE = 'scrims_registration_settings.json'
SCRIMS_FILE = 'scrims.json'

# Initialize data dictionaries
registration_settings = {}
ss_verify_files = {}
tournaments = {}
scrims = {}
scrims_registration_settings = {}

# Helper function to load JSON data
def load_json_file(file_path):
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {file_path}, initializing as empty dictionary.")
                return {}
    return {}

# Helper function to save JSON data
def save_json_file(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

# Load data from JSON files
def load_data():
    global registration_settings, ss_verify_files, tournaments, scrims, scrims_registration_settings
    
    registration_settings = load_json_file(REGISTRATION_SETTINGS_FILE)
    ss_verify_files = load_json_file(SS_VERIFY_FILES_FILE)
    tournaments = load_json_file(TOURNAMENTS_FILE)
    scrims = load_json_file(SCRIMS_FILE)
    load_scrims_registration_settings()

# Save specific data to JSON files
def save_registration_settings():
    save_json_file(REGISTRATION_SETTINGS_FILE, registration_settings)

def save_ss_verify_files():
    save_json_file(SS_VERIFY_FILES_FILE, ss_verify_files)

def save_tournaments():
    save_json_file(TOURNAMENTS_FILE, tournaments)

# Serialization and Deserialization for Scrims
"""def serialize_scrims(scrims_data):
    serialized_data = {}
    for key, value in scrims_data.items():
        serialized_data[key] = {
            "role_id": value.get("role").id if value.get("role") else None,  # Serialize the Role object to role_id
            "other_data": value.get("other_data", {})  # Use an empty dictionary as default if 'other_data' is missing
        }
    return serialized_data

def deserialize_scrims(serialized_data):
    deserialized_data = {}
    for key, value in serialized_data.items():
        deserialized_data[key] = {
            "role": client.get_role(value["role_id"]) if value.get("role_id") else None,  # Deserialize role_id back to Role object
            "other_data": value["other_data"],  # Assuming other_data is deserializable
        }
    return deserialized_data"""

# Serialization and Deserialization for Scrims
def serialize_scrims(scrims_data):
    serialized_data = {}
    for scrim_id, scrim in scrims_data.items():
        serialized_data[scrim_id] = {
            "category_id": scrim.get("category_id"),
            "scrim_name": scrim.get("scrim_name"),
            "role_id": scrim.get("role").id if scrim.get("role") else None,  # Serialize the Role object to role_id
            "channel_id": scrim.get("channel").id if scrim.get("channel") else None,  # Serialize the Channel object to channel_id
            "idp_channel_id": scrim.get("idp").id if scrim.get("idp") else None,  # Serialize the IDP Channel object to idp_channel_id
            "start_time": scrim.get("start_time").strftime("%Y-%m-%d %H:%M:%S") if isinstance(scrim.get("start_time"), datetime) else None,  # Serialize start_time to string with full datetime format
            "other_data": scrim.get("other_data", {})  # Use an empty dictionary as default if 'other_data' is missing
        }
    return serialized_data

def deserialize_scrims(serialized_data, client):
    deserialized_data = {}
    for scrim_id, scrim in serialized_data.items():
        deserialized_data[scrim_id] = {
            "category_id": scrim.get("category_id"),
            "scrim_name": scrim.get("scrim_name"),
            "role": client.get_role(scrim.get("role_id")) if scrim.get("role_id") else None,  # Deserialize role_id back to Role object
            "channel": client.get_channel(scrim.get("channel_id")) if scrim.get("channel_id") else None,  # Deserialize channel_id back to Channel object
            "idp": client.get_channel(scrim.get("idp_channel_id")) if scrim.get("idp_channel_id") else None,  # Deserialize idp_channel_id back to Channel object
            "start_time": datetime.strptime(scrim.get("start_time"), "%Y-%m-%d %H:%M:%S") if scrim.get("start_time") else None,  # Deserialize start_time back to datetime object
            "other_data": scrim.get("other_data", {})  # Assuming other_data is deserializable
        }
    return deserialized_data

def save_scrims():
    serialized_scrims = serialize_scrims(scrims)
    save_json_file(SCRIMS_FILE, serialized_scrims)

def load_scrims():
    global scrims
    loaded_scrims = load_json_file(SCRIMS_FILE)
    scrims = deserialize_scrims(loaded_scrims)

def save_scrims_registration_settings():
    serialized_settings = {
        category_id: {
            "scrim_times": serialize_scrim_times(settings.get("scrim_times", [])),
            "other_info": settings.get("other_info", ""),  # Provide default empty string if 'other_info' is missing
            "ping_role": serialize_ping_role(settings.get("ping_role").id) if settings.get("ping_role") else None ,   # Save ping_role as is (None or a valid role ID/name)
            "slots": settings.get("slots", 0),  # Default to 0 if slots are missing
            "mentions_required": settings.get("mentions_required", False),  # Default to False if not set
            "num_scrims": settings.get("num_scrims", 0)  # Default to 0 if num_scrims is missing
        }
        for category_id, settings in scrims_registration_settings.items()
    }
    save_json_file(SCRIMS_REG_SETTINGS_FILE, serialized_settings)

# Convert datetime.time to string for serialization
def serialize_scrim_times(scrim_times):
    return [time.strftime("%H:%M") for time in scrim_times]

# Convert string back to datetime.time for deserialization
def deserialize_scrim_times(scrim_times_str):
    return [datetime.strptime(time_str, "%H:%M").time() for time_str in scrim_times_str]

def serialize_ping_role(ping_role):
    serialized_data = {}
    for key, value in ping_role.items():
        serialized_data[key] = {
            "ping_role_id": value.get("ping_role").id if value.get("ping_role") else None,  # Serialize the Role object to role_id
        }
    return serialized_data

def deserialize_ping_role(serialized_data):
    deserialized_data = {}
    for key, value in serialized_data.items():
        deserialized_data[key] = {
            "ping_role": client.get_role(value["ping_role_id"]) if value.get("ping_role_id") else None,  # Deserialize role_id back to Role object
        }
    return deserialized_data


def load_scrims_registration_settings():
    global scrims_registration_settings
    loaded_settings = load_json_file(SCRIMS_REG_SETTINGS_FILE)
    scrims_registration_settings = {
        category_id: {
            "scrim_times": deserialize_scrim_times(settings.get("scrim_times", [])),
            "other_info": settings.get("other_info", ""),  # Provide default empty string if 'other_info' is missing
            "ping_role": deserialize_ping_role( id=settings.get("ping_role")) if settings.get("ping_role") else None,  # Convert ID back to role object,  # Load ping_role as is (None or a valid role ID/name)
            "slots": settings.get("slots", 0),  # Default to 0 if slots are missing
            "mentions_required": settings.get("mentions_required", False),  # Default to False if not set
            "num_scrims": settings.get("num_scrims", 0)  # Default to 0 if num_scrims is missing
        }
        for category_id, settings in loaded_settings.items()
    }


def save_registration_and_tournaments():
    save_registration_settings()
    save_tournaments()

# Load existing data or initialize new data structures
load_data()

class CreatetournamentCategoryModal(Modal):
    def __init__(self):
        super().__init__(title="Create New Category")
        self.add_item(TextInput(label="Category Name", placeholder="Enter the new category name", custom_id="category_name"))

    async def on_submit(self, interaction: discord.Interaction):
        category_name = self.children[0].value
        category = await interaction.guild.create_category(category_name)
        await interaction.response.send_message(f"Category '{category_name}' created.", ephemeral=True)
        await create_troles(interaction, category)
        await create_toptional_channels(interaction, category)

class SelecttournamentCategoryAction(View):
    def __init__(self):
        super().__init__()
        self.add_item(SelecttCategory())

class SelecttCategory(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Create New Category", value="create_new"),
            discord.SelectOption(label="Select Existing Category", value="select_existing")
        ]
        super().__init__(placeholder="Choose an action...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "create_new":
            await interaction.response.send_modal(CreatetournamentCategoryModal())
        elif self.values[0] == "select_existing":
            options = [discord.SelectOption(label=category.name, value=str(category.id)) for category in interaction.guild.categories]
            view = View()
            view.add_item(SelectExistingtCategoryDropdown(options))
            await interaction.response.send_message("Select an existing category:", view=view)

class SelectExistingtCategoryDropdown(Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category_id = int(self.values[0])
        category = discord.utils.get(interaction.guild.categories, id=category_id)
        await create_troles(interaction, category)
        await interaction.message.edit(content=f"Category '{category.name}' selected.", view=None)
        await create_toptional_channels(interaction, category)
        self.view.stop()

async def create_troles(interaction, category):
    guild = interaction.guild
    tournament_manager = await guild.create_role(name=f"{category.name} Tournament Manager")
    confirmed_team = await guild.create_role(name=f"{category.name} Confirmed")
    await interaction.channel.send(f"Roles '{tournament_manager.name}' and '{confirmed_team.name}' created.")
    save_tournaments()  # Save data after change

async def create_toptional_channels(interaction, category):
    guild = interaction.guild
    channels = ["INFO", "UPDATES", "REGISTER HERE", "CONFIRMED TEAMS", "QUERIES", "HELP VC"]
    for channel in channels:
        text_channel = await guild.create_text_channel(channel, category=category)
        if channel in ["INFO", "UPDATES", "CONFIRMED TEAMS"]:
            await text_channel.set_permissions(guild.default_role, read_messages=True, send_messages=False)
            for role in guild.roles:
                if role.permissions.administrator or role.name == f"{category.name} Tournament Manager":
                    await text_channel.set_permissions(role, read_messages=True, send_messages=True)
    await interaction.channel.send(f"Required channels created in '{category.name}'.")
    await ask_tregistration_settings(interaction, category)

async def ask_tregistration_settings(interaction: discord.Interaction, category: discord.CategoryChannel):
    await interaction.channel.send("Please enter the number of slots (min 12, max 1000):")

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        slots_msg = await client.wait_for('message', check=check, timeout=300)
        slots = int(slots_msg.content)
        if 12 <= slots <= 1000:
            await interaction.channel.send("Please enter the number of mentions required for registration (min 0, max 10):")
            mentions_msg = await client.wait_for('message', check=check, timeout=300)
            mentions_required = int(mentions_msg.content)
            if 0 <= mentions_required <= 10:
                registration_settings[category.id] = {"slots": slots, "mentions_required": mentions_required}
                save_registration_settings()  # Save data after changes
                await interaction.channel.send(f"Registration settings: {slots} slots, {mentions_required} mentions required.")
                await ask_tslots_per_group(interaction, category)
            else:
                await interaction.channel.send("Invalid input for mentions. Please try again.")
                await ask_tregistration_settings(interaction, category)
        else:
            await interaction.channel.send("Invalid input for slots. Please try again.")
            await ask_tregistration_settings(interaction, category)
    except TimeoutError:
        await interaction.channel.send("You took too long to respond. Please start over.")

async def ask_tslots_per_group(interaction: discord.Interaction, category: discord.CategoryChannel):
    await interaction.channel.send("Please enter the number of slots per group (max 25):")

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        slots_per_group_msg = await client.wait_for('message', check=check, timeout=300)
        slots_per_group = int(slots_per_group_msg.content)
        if 1 <= slots_per_group <= 25:
            registration_settings[category.id]["slots_per_group"] = slots_per_group
            save_registration_settings()  # Save data after changes
            await interaction.channel.send(f"Slots per group set to {slots_per_group}.")
            await ask_ss_verify(interaction, category)
        else:
            await interaction.channel.send("Invalid input for slots per group. Please try again.")
            await ask_tslots_per_group(interaction, category)
    except TimeoutError:
        await interaction.channel.send("You took too long to respond. Please start over.")

async def ask_ss_verify(interaction: discord.Interaction, category: discord.CategoryChannel):
    view = ConfirmSSVerifyView(category)
    await interaction.channel.send("Do you want to add 'SS VERIFY'?", view=view)

class ConfirmSSVerifyView(View):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.add_item(ConfirmSSVerifyButton(label="Yes", style=discord.ButtonStyle.green, category=category))
        self.add_item(ConfirmSSVerifyButton(label="No", style=discord.ButtonStyle.red, category=category))

class ConfirmSSVerifyButton(Button):
    def __init__(self, label, style, category):
        super().__init__(label=label, style=style)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
        # Delete the message and buttons after interaction
        await interaction.message.delete()
        
        if self.label == "Yes":
            await interaction.response.send_message("Please enter the number of screenshots required (0-100):")

            def check(m):
                return m.author == interaction.user and m.channel == interaction.channel

            try:
                ss_msg = await client.wait_for('message', check=check, timeout=300)
                ss_required = int(ss_msg.content)
                if 0 <= ss_required <= 100:
                    ss_verified_role = await interaction.guild.create_role(name=f"{self.category.name} SS Verified")
                    registration_settings[self.category.id]["ss_required"] = ss_required
                    await interaction.channel.send(f"SS Verify settings: {ss_required} screenshots required. Role '{ss_verified_role.name}' created.")
                    await interaction.guild.create_text_channel("SS VERIFY", category=self.category)
                    await interaction.channel.send("Channel 'SS VERIFY' created.")
                    await ask_tag_check(interaction, self.category)
                else:
                    await interaction.channel.send("Invalid input for screenshots. Please try again.")
                    await ask_ss_verify(interaction, self.category)
            except TimeoutError:
                await interaction.channel.send("You took too long to respond. Please start over.")
        else:
            await ask_tag_check(interaction, self.category)

async def ask_tag_check(interaction: discord.Interaction, category: discord.CategoryChannel):
    view = ConfirmTagCheckView(category)
    await interaction.channel.send("Do you want to add 'TAG CHECK'?", view=view)

class ConfirmTagCheckView(View):
    def __init__(self, category):
        super().__init__()
        self.category = category
        self.add_item(ConfirmTagCheckButton(label="Yes", style=discord.ButtonStyle.green, category=category))
        self.add_item(ConfirmTagCheckButton(label="No", style=discord.ButtonStyle.red, category=category))

class ConfirmTagCheckButton(Button):
    def __init__(self, label, style, category):
        super().__init__(label=label, style=style)
        self.category = category

    async def callback(self, interaction: discord.Interaction):
           # Delete the message and buttons after interaction
        await interaction.message.delete()
        

        if self.label == "Yes":
            await interaction.guild.create_text_channel("TAG CHECK", category=self.category)
            await interaction.channel.send("Channel 'TAG CHECK' created.")
        else:
            await interaction.channel.send("Skipping 'TAG CHECK' channel creation.")

        """tournament_id = generate_tournament_id()
        tournaments[tournament_id] = self.category.id
        await interaction.channel.send(f"Setup complete. Your unique tournament ID is: {tournament_id}")"""

        async def send_tournament_setup_embed(interaction: discord.Interaction, tournament_id: str):
           embed = discord.Embed(
        title="Tournament Setup Complete",
        description="Your tournament has been successfully set up.",
        color=0xC45AEC
    )
           embed.add_field(name="Tournament ID", value=f"`{tournament_id}`", inline=False)
           embed.set_footer(text="Use this ID to manage your tournament.")
           save_registration_and_tournaments()  # Save data after changes
           await interaction.channel.send(embed=embed)



        tournament_id = generate_tournament_id()
        tournaments[tournament_id] = self.category.id
    
        await send_tournament_setup_embed(interaction, tournament_id)
            

def generate_tournament_id():
    return ''.join(random.choices(string.digits, k=4))

async def create_proxima_category(interaction: discord.Interaction):
    guild = interaction.guild

    # Create the Proxima Mod role with administrator permissions
    proxima_mod = await guild.create_role(name="Proxima Mod", permissions=Permissions(administrator=True))

    # Get the administrator role
    admin_role = guild.default_role
    for role in guild.roles:
        if role.permissions.administrator:
            admin_role = role
            break

    # Create the Proxima Private category
    overwrites = {
        guild.default_role: PermissionOverwrite(view_channel=False),  # Deny access to everyone else
        admin_role: PermissionOverwrite(view_channel=True),           # Allow access to administrators
        proxima_mod: PermissionOverwrite(view_channel=True)           # Allow access to Proxima Mod role
    }
    proxima_category = await guild.create_category("Proxima Private", overwrites=overwrites)

    # Create the Proxima Announcements and Proxima Logs channels within the Proxima Private category
    proxima_announcements= await guild.create_text_channel("Proxima Announcements", category=proxima_category, overwrites=overwrites)
    await guild.create_text_channel("Proxima Logs", category=proxima_category, overwrites=overwrites)
    await interaction.channel.send("Proxima Private category, Proxima Announcements, Proxima Logs channels, and Proxima Mod role created.")
    await send_proxima_announcements_embed(proxima_announcements)

async def send_proxima_announcements_embed(channel):
    embed = discord.Embed(title="Proxima Tournament Settings", description="Use the buttons below to manage the tournament settings.", color=0xC45AEC)
    view = ProximaAnnouncementsView()
    await channel.send(embed=embed, view=view)

#button of tournament

class ProximaAnnouncementsView(View):
    def __init__(self):
        super().__init__(timeout=None)
    

    @discord.ui.button(label="Add Slots", style=discord.ButtonStyle.green)
    async def add_slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChangeSlotsModal(action="add"))

    @discord.ui.button(label="Cancel Slots", style=discord.ButtonStyle.red)
    async def cancel_slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChangeSlotsModal(action="cancel"))

    @discord.ui.button(label="Change Slots Per Group", style=discord.ButtonStyle.blurple)
    async def change_group_slots(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChangeGroupSlotsModal())

    @discord.ui.button(label="Change Mentions Required", style=discord.ButtonStyle.blurple)
    async def change_mentions_required(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ChangeMentionsModal())

class ChangeSlotsModal(Modal):
    def __init__(self, action):
        super().__init__(title=f"{action.capitalize()} Slots")
        self.action = action
        self.add_item(TextInput(label="Tournament ID", placeholder="Enter 4-digit Tournament ID", custom_id="tournament_id"))
        self.add_item(TextInput(label="Number of Slots", placeholder="Enter number of slots", custom_id="slots"))

    async def on_submit(self, interaction: discord.Interaction):
        tournament_id = self.children[0].value
        if tournament_id in tournaments:
            slots = int(self.children[1].value)
            category_id = tournaments[tournament_id]
            if category_id:
                settings = registration_settings[category_id]
                if self.action == "add":
                    settings["slots"] += slots
                elif self.action == "cancel":
                    settings["slots"] -= slots
                    settings["slots"] = max(0, settings["slots"])  # Ensure slots do not go negative
                await interaction.response.send_message(f"{self.action.capitalize()}ed {slots} slots.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid Tournament ID.", ephemeral=True)

class ChangeGroupSlotsModal(Modal):
    def __init__(self):
        super().__init__(title="Change Slots Per Group")
        self.add_item(TextInput(label="Tournament ID", placeholder="Enter 4-digit Tournament ID", custom_id="tournament_id"))
        self.add_item(TextInput(label="Slots Per Group", placeholder="Enter number of slots per group", custom_id="slots_per_group"))

    async def on_submit(self, interaction: discord.Interaction):
        tournament_id = self.children[0].value
        if tournament_id in tournaments:
            slots_per_group = int(self.children[1].value)
            category_id = tournaments[tournament_id]
            if category_id:
                registration_settings[category_id]["slots_per_group"] = slots_per_group
                await interaction.response.send_message(f"Updated slots per group to {slots_per_group}.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid Tournament ID.", ephemeral=True)

class ChangeMentionsModal(Modal):
    def __init__(self):
        super().__init__(title="Change Mentions Required")
        self.add_item(TextInput(label="Tournament ID", placeholder="Enter 4-digit Tournament ID", custom_id="tournament_id"))
        self.add_item(TextInput(label="Mentions Required", placeholder="Enter number of mentions required", custom_id="mentions_required"))

    async def on_submit(self, interaction: discord.Interaction):
        tournament_id = self.children[0].value
        if tournament_id in tournaments:
            mentions_required = int(self.children[1].value)
            category_id = tournaments[tournament_id]
            if category_id:
                registration_settings[category_id]["mentions_required"] = mentions_required
                await interaction.response.send_message(f"Updated mentions required to {mentions_required}.", ephemeral=True)
        else:
            await interaction.response.send_message("Invalid Tournament ID.", ephemeral=True)

"""class ProximaSettingsView(View):
    def __init__(self):
        super().__init__()
        self.add_item(ProximaSettingsButton(label="Edit Tournament Settings", style=discord.ButtonStyle.primary))
        self.add_item(ProximaSettingsButton(label="Create Tournament", style=discord.ButtonStyle.success))

class ProximaSettingsButton(Button):
    def __init__(self, label, style):
        super().__init__(label=label, style=style)

    async def callback(self, interaction: discord.Interaction):
        if self.label == "Edit Tournament Settings":
            # Logic to edit tournament settings
            await interaction.response.send_message("Edit Tournament Settings functionality is not yet implemented.", ephemeral=True)
        elif self.label == "Create Tournament":
            # Logic to create a new tournament
            await interaction.response.send_message("Create Tournament functionality is not yet implemented.", ephemeral=True)"""

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    await handle_tregistration(message)
    await handle_ss_verify(message)
    await handle_tag_check(message)
    await client.process_commands(message)

async def handle_tregistration(message):
    if message.channel.name == "register here":
        category_id = message.channel.category_id
        settings = registration_settings.get(category_id)
        if settings:
            mentions = message.mentions
            if len(mentions) == settings["mentions_required"]:
                embed = discord.Embed(title="Team Registered", description=f"Team Name: {message.content.split()[0]}", color=0xC45AEC)
                embed.add_field(name="Members", value=", ".join([mention.mention for mention in mentions]), inline=False)
                confirmed_channel = discord.utils.get(message.guild.text_channels, name="confirmed teams", category=message.channel.category)
                await confirmed_channel.send(embed=embed)
                confirmed_role = discord.utils.get(message.guild.roles, name=f"{message.channel.category.name} Confirmed")
                for mention in mentions:
                    await mention.add_roles(confirmed_role)
                await message.add_reaction("✅")
                await handle_group_assignment(message, category_id)
            else:
                proxima_logs = discord.utils.get(message.guild.text_channels, name="proxima logs", category=message.channel.category)
                embed = discord.Embed(title="Registration Failed", description=f"Team Name: {message.content.split()[0]}", color=0xC45AEC)
                embed.add_field(name="Error", value=f"Required mentions: {settings['mentions_required']}, but got {len(mentions)}.", inline=False)
                await proxima_logs.send(embed=embed)
                await message.add_reaction("❌")

async def handle_group_assignment(message, category_id):
    settings = registration_settings.get(category_id)
    if settings:
        total_slots = settings["slots"]
        slots_per_group = settings["slots_per_group"]
        group_count = (total_slots + slots_per_group - 1) // slots_per_group  # Ceiling division
        group_names = [f"GRP {chr(65 + i)}" for i in range(group_count)]  # GRP A, GRP B, ...

        # Assign group roles and create group channels if not exist
        for i, group_name in enumerate(group_names):
            group_role = discord.utils.get(message.guild.roles, name=group_name)
            if not group_role:
                group_role = await message.guild.create_role(name=group_name)
            group_channel = discord.utils.get(message.guild.text_channels, name=f"group {chr(65 + i)}", category=message.channel.category)
            if not group_channel:
                await message.guild.create_text_channel(f"group {chr(65 + i)}", category=message.channel.category)

        # Assign group role to team members
        group_index = sum(len(role.members) for role in message.guild.roles if role.name in group_names) // slots_per_group
        group_role = discord.utils.get(message.guild.roles, name=group_names[group_index])
        for mention in message.mentions:
            await mention.add_roles(group_role)
        await message.channel.send(f"Team assigned to {group_role.name}.")
        save_registration_settings()  # Save data after changes

async def handle_ss_verify(message):
    if message.channel.name == "ss verify":
        category_id = message.channel.category_id
        settings = registration_settings.get(category_id)
        if settings:
            if len(message.attachments) == settings["ss_required"]:
                unique_files = set(attachment.filename for attachment in message.attachments)
                if len(unique_files) == len(message.attachments):
                    ss_verified_role = discord.utils.get(message.guild.roles, name=f"{message.channel.category.name} SS Verified")
                    await message.author.add_roles(ss_verified_role)
                    await message.add_reaction("✅")
                    save_ss_verify_files()
                else:
                    duplicate_files = [attachment.filename for attachment in message.attachments if attachment.filename in ss_verify_files]
                    proxima_logs = discord.utils.get(message.guild.text_channels, name="proxima logs", category=message.channel.category)
                    embed = discord.Embed(title="SS Verify Failed", description=f"User: {message.author.mention}", color=0xC45AEC)
                    embed.add_field(name="Error", value=f"Duplicate files: {', '.join(duplicate_files)}.", inline=False)
                    await proxima_logs.send(embed=embed)
                    await message.add_reaction("❌")
                    save_ss_verify_files()
            else:
                proxima_logs = discord.utils.get(message.guild.text_channels, name="proxima logs", category=message.channel.category)
                embed = discord.Embed(title="SS Verify Failed", description=f"User: {message.author.mention}", color=0xC45AEC)
                embed.add_field(name="Error", value=f"Required screenshots: {settings['ss_required']}, but got {len(message.attachments)}.", inline=False)
                await proxima_logs.send(embed=embed)
                await message.add_reaction("❌")
                save_ss_verify_files()

async def handle_tag_check(message):
    if message.channel.name == "tag check":
        category_id = message.channel.category_id
        settings = registration_settings.get(category_id)
        if settings:
            mentions = message.mentions
            if len(mentions) == settings["mentions_required"]:
                await message.add_reaction("✅")
            else:
                proxima_logs = discord.utils.get(message.guild.text_channels, name="proxima logs", category=message.channel.category)
                embed = discord.Embed(title="Tag Check Failed", description=f"User: {message.author.mention}", color=0xC45AEC)
                embed.add_field(name="Error", value=f"Required mentions: {settings['mentions_required']}, but got {len(mentions)}.", inline=False)
                await proxima_logs.send(embed=embed)
                await message.add_reaction("❌")

@client.command()
@commands.has_permissions(administrator=True)
async def setup(ctx):                     #setup command
    await create_proxima_category(ctx)

@client.command()
@commands.has_permissions(administrator=True)
async def tsetup(ctx):               #tournament setup command
    view = SelecttournamentCategoryAction()
    await ctx.send("Do you want to create a new tournament or edit an existing one?", view=view)
    save_tournaments()  # Save data after changes

@client.command()
@commands.has_permissions(administrator=True)
async def sttorny(ctx, tournament_id: str): #start tournament
    category_id = tournaments.get(tournament_id)
    if category_id:
        category = discord.utils.get(ctx.guild.categories, id=category_id)
        await ctx.send(f"Tournament with ID {tournament_id} has started in category '{category.name}'.")
    else:
        await ctx.send(f"No tournament found with ID {tournament_id}.")
        save_tournaments()  # Save data after changes


@client.command()
@commands.has_permissions(administrator=True)
async def sptorny(ctx, tournament_id: str): #stop tournament
    category_id = tournaments.pop(tournament_id, None)
    if category_id:
        category = discord.utils.get(ctx.guild.categories, id=category_id)
        await ctx.send(f"Tournament with ID {tournament_id} has stopped in category '{category.name}'.")
        save_tournaments()  # Save data after changes
    else:
        await ctx.send(f"No tournament found with ID {tournament_id}.")


        #scrims from here 


class CreatesCategoryModal(Modal):
    def __init__(self):
        super().__init__(title="Create New Category")
        self.add_item(TextInput(label="Category Name", placeholder="Enter the new category name", custom_id="category_name"))

    async def on_submit(self, interaction: discord.Interaction):
        category_name = self.children[0].value
        category = await interaction.guild.create_category(category_name)
        await interaction.response.send_message(f"Category '{category_name}' created.", ephemeral=True)
        await create_roles(interaction, category)
        await create_optional_channels(interaction, category)

class SelectCategoryAction(View):
    def __init__(self):
        super().__init__()
        self.add_item(SelectCategory())

class SelectCategory(Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Create New Category", value="create_new"),
            discord.SelectOption(label="Select Existing Category", value="select_existing")
        ]
        super().__init__(placeholder="Choose an action...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "create_new":
            await interaction.response.send_modal(CreatesCategoryModal())
        elif self.values[0] == "select_existing":
            options = [discord.SelectOption(label=category.name, value=str(category.id)) for category in interaction.guild.categories]
            view = View()
            view.add_item(SelectExistingCategoryDropdown(options))
            await interaction.response.send_message("Select an existing category:", view=view)

class SelectExistingCategoryDropdown(Select):
    def __init__(self, options):
        super().__init__(placeholder="Choose a category...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category_id = int(self.values[0])
        category = discord.utils.get(interaction.guild.categories, id=category_id)
        await create_roles(interaction, category)
        await interaction.message.edit(content=f"Category '{category.name}' selected.", view=None)
        await create_optional_channels(interaction, category)
        self.view.stop()

async def create_roles(interaction, category):
    guild = interaction.guild
    scrims_manager = await guild.create_role(name=f"{category.name} scrims Manager")
    await interaction.channel.send(f"Role '{scrims_manager.name}' created.")

async def create_optional_channels(interaction, category):
    guild = interaction.guild
    channels = ["INFO", "UPDATES", "RULES", "HOW TO REGISTER", "SCHEDULE", "RESULTS", "LOBBY-SS", "BAN TEAMS", "CANCEL CLAIM SLOTS"]
    for channel in channels:
        text_channel = await guild.create_text_channel(channel, category=category)
        if channel in ["INFO", "UPDATES", "RULES", "HOW TO REGISTER", "SCHEDULE", "RESULTS", "LOBBY-SS", "BAN TEAMS", "CANCEL CLAIM SLOTS"]:
            await text_channel.set_permissions(guild.default_role, read_messages=True, send_messages=False)
            for role in guild.roles:
                if role.permissions.administrator or role.name == f"{category.name} scrims Manager":
                    await text_channel.set_permissions(role, read_messages=True, send_messages=True)
    await interaction.channel.send(f"Optional channels created in '{category.name}'.")
    await ask_scrims_registration_settings(interaction, category)

async def ask_scrims_registration_settings(interaction: discord.Interaction, category: discord.CategoryChannel):
    await interaction.channel.send("Please enter the number of slots (min 12, max 25):")

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        slots_msg = await client.wait_for('message', check=check, timeout=300)
        slots = int(slots_msg.content)
        if 12 <= slots <= 25:
            await interaction.channel.send("Please enter the number of scrims to create (max 10):")
            scrims_msg = await client.wait_for('message', check=check, timeout=300)
            num_scrims = int(scrims_msg.content)
            if 1 <= num_scrims <= 10:
                await interaction.channel.send("Please enter the number of mentions required for successful registration (max 10):")
                mentions_msg = await client.wait_for('message', check=check, timeout=300)
                mentions_required = int(mentions_msg.content)
                if 0 <= mentions_required <= 10:
                    scrims_registration_settings[category.id]= {"slots": slots, "mentions_required": mentions_required, "num_scrims": num_scrims}
                    await interaction.channel.send("Please enter the start time for each scrim in 24-hour format (e.g., 14:30):")
                    scrim_times = []
                    for i in range(num_scrims):
                        time_msg = await client.wait_for('message', check=check, timeout=300)
                        try:
                            scrim_time = datetime.strptime(time_msg.content, "%H:%M").time()
                            scrim_times.append(scrim_time)
                        except ValueError:
                            await interaction.channel.send("Invalid time format. Please enter again.")
                            i -= 1
                    scrims_registration_settings[category.id]["scrim_times"] = scrim_times
                    await interaction.channel.send("Please mention the role to ping during scrim start:")
                    role_msg = await client.wait_for('message', check=check, timeout=300)
                    role = discord.utils.get(interaction.guild.roles, mention=role_msg.content)
                    scrims_registration_settings[category.id]["ping_role"] = role
                    # Save the registration settings after they are fully set
                    save_scrims_registration_settings()
                    await create_scrims(interaction, category, num_scrims)
                else:
                    await interaction.channel.send("Invalid input for mentions. Please try again.")
                    await ask_scrims_registration_settings(interaction, category)
            else:
                await interaction.channel.send("Invalid input for number of scrims. Please try again.")
                await ask_scrims_registration_settings(interaction, category)
        else:
            await interaction.channel.send("Invalid input for slots. Please try again.")
            await ask_scrims_registration_settings(interaction, category)
    except TimeoutError:
        await interaction.channel.send("You took too long to respond. Please start over.")

async def create_scrims(interaction, category, num_scrims):
    for i in range(1, num_scrims + 1):
        await interaction.channel.send(f"Please enter the name for Scrim {i}:")
        def check(m):
            return m.author == interaction.user and m.channel == interaction.channel

        try:
            scrim_name_msg = await client.wait_for('message', check=check, timeout=300)
            scrim_name = scrim_name_msg.content

            scrim_role = await interaction.guild.create_role(name=f"{scrim_name} IDP")
            scrim_channel = await interaction.guild.create_text_channel(f"{scrim_name}-registration", category=category)
            idp_channel = await interaction.guild.create_text_channel(f"{scrim_name}-idp", category=category)
            await idp_channel.set_permissions(interaction.guild.default_role, read_messages=True, send_messages=False)
            await idp_channel.set_permissions(scrim_role, read_messages=True, send_messages=True)
            
            scrim_id = generate_scrim_id()
            scrims[scrim_id] = {
                "category_id": category.id, 
                "scrim_name": scrim_name, 
                "role": scrim_role, 
                "channel": scrim_channel,
                "idp": idp_channel,
                "start_time": scrims_registration_settings[category.id]["scrim_times"][i-1]
            }
            # Save the scrims data after creating all scrims
            save_scrims()

            async def send_scrim_creation_embed(interaction: discord.Interaction, scrim_name: str, scrim_id: str):
                 # Create the embed message
                 embed = discord.Embed(
        title="Scrim Created",
        description=f"A new scrim has been created.",
        color=0xC45AEC  # Customize the color as needed
        )
                 # Add fields to the embed
                 embed.add_field(name="Scrim Name", value=scrim_name, inline=False)
                 embed.add_field(name="Scrim ID", value=scrim_id, inline=False)
                 # Set the footer text
                 embed.set_footer(text="Use this ID to manage your scrim.")
                 # Send the embed to the interaction channel
                 await interaction.channel.send(embed=embed)
            
            await send_scrim_creation_embed(interaction, scrim_name, scrim_id)
            await send_registration_embed(scrim_channel, scrim_name, scrims_registration_settings[category.id]["mentions_required"], scrims_registration_settings[category.id].get("ping_role"))

        except TimeoutError:
            await interaction.channel.send("You took too long to respond. Please start over.")
    
    schedule_scrims.start()
@tasks.loop(minutes=1)
async def schedule_scrims():
    now = datetime.now().time()
    for scrim in scrims:  # Assuming scrims is a list or dictionary of scrim data
        start_time = scrim.get("start_time")
        if start_time is not None:
            scrim_start_datetime = datetime.combine(datetime.today(), start_time)
            if start_time <= now < (scrim_start_datetime + timedelta(minutes=1)).time():
                # Perform your scheduled task actions here
                pass

async def start_scrim(scrim_id):
    scrim = scrims[scrim_id]
    channel = scrim["channel"]
    role_to_mention = scrims_registration_settings[scrim["category_id"]]["ping_role"]
    await channel.send(f"{role_to_mention.mention}, Scrim '{scrim['scrim_name']}' is starting now!")
    await auto_clean_registration_channel(channel)

async def send_registration_embed(channel, scrim_name, mentions_required, ping_role):
    embed = discord.Embed(
        title=f"Registration Open: {scrim_name}",
        description=f"Registration is now open! Do register.\n"
                    f"**Mentions Required:** {mentions_required}\n"
                    f"**Role to Mention:** {ping_role.mention}" if ping_role else "**Role to Mention:** None",
        color=0xC45AEC
    )
    await channel.send(embed=embed)

async def auto_clean_registration_channel(channel):
    await channel.send("This channel will be cleaned automatically in 12 hours.")
    await discord.utils.sleep_until(datetime.now() + timedelta(hours=12))
    await channel.purge()

async def handle_registration(message):
    category_id = message.channel.category_id
    scrim_id = None
    for sid, scrim in scrims.items():
        if scrim["channel"].id == message.channel.id:
            scrim_id = sid
            break

    if scrim_id:
        settings = scrims_registration_settings.get(category_id)
        if settings:
            mentions = message.mentions
            if len(mentions) == settings["mentions_required"]:
                # Get the team name
                team_name = message.content.split()[0]
                
                # Add team to the scrim's list
                scrim.setdefault("teams", []).append(team_name)

                # Add role to the members
                confirmed_role = discord.utils.get(message.guild.roles, name=f"{scrim['scrim_name']} idp")
                for mention in mentions:
                    await mention.add_roles(confirmed_role)
                
                # React with a tick mark
                await message.add_reaction("✅")

                # If all slots are filled, send the final embed message
                if len(scrim["teams"]) >= settings["slots"]:
                    embed_description = "\n".join(
                        [f"Slot {i+1:02d} -> {team}" for i, team in enumerate(scrim["teams"])]
                    )
                    embed = discord.Embed(
                        title=f"{scrim['scrim_name']} Slots",
                        description=embed_description,
                        color=0xC45AEC
                    )
                    await message.channel.send(embed=embed)

            else:
                # React with a cross mark if the number of mentions is incorrect
                await message.add_reaction("❌")

                # Send an error message to a logs channel
                proxima_logs = discord.utils.get(message.guild.text_channels, name="proxima logs", category=message.channel.category)
                embed = discord.Embed(
                    title="Registration Failed",
                    description=f"Team Name: {message.content.split()[0]}",
                    color=0xC45AEC
                )
                embed.add_field(name="Error", value=f"Required mentions: {settings['mentions_required']}, but got {len(mentions)}.", inline=False)
                await proxima_logs.send(embed=embed)


"""async def send_proxima_announcements_embed(category):
    proxima_announcements = discord.utils.get(category.guild.text_channels, name="proxima announcements")
    if not proxima_announcements:
        proxima_announcements = await category.guild.create_text_channel("proxima announcements", category=category)

    embed = discord.Embed(title="Proxima Tournament Settings", description="Use the buttons below to manage the tournament settings.", color=0xC45AEC)
    view = ProximaSettingsView()
    await proxima_announcements.send(embed=embed, view=view)

class ProximaSettingsView(View):
    def __init__(self):
        super().__init__()
        self.add_item(ProximaSettingsButton(label="Add Scrim"))
        self.add_item(ProximaSettingsButton(label="Remove Scrim"))

class ProximaSettingsButton(Button):
    def __init__(self, label):
        super().__init__(label=label, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Button '{self.label}' clicked.", ephemeral=True)"""

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.channel.category and "registration" in message.channel.name:
        await handle_registration(message)
    await client.process_commands(message)

@client.command(name="ssetup")
async def scrimsetup(ctx):
    view= SelectCategoryAction()
    await ctx.send("Scrim setup initiated.",view=view)

@client.command(name="sttscrim")
async def start_scrim_command(ctx, scrim_id: str):
    if scrim_id in scrims:
        await start_scrim(scrim_id)
        await ctx.send(f"Scrim with ID {scrim_id} has been forcefully started.")
    else:
        await ctx.send(f"No scrim found with ID {scrim_id}.")

@client.command(name="spscrim")
async def stop_scrim_command(ctx, scrim_id: str):
    if scrim_id in scrims:
        await stop_scrim(scrim_id)
        await ctx.send(f"Scrim with ID {scrim_id} has been forcefully stopped.")
    else:
        await ctx.send(f"No scrim found with ID {scrim_id}.")

@client.command(name="dlscrim")
async def delete_scrim_command(ctx, scrim_id: str):
    if scrim_id in scrims:
        await delete_scrim(scrim_id)
        await ctx.send(f"Scrim with ID {scrim_id} has been deleted.")
    else:
        await ctx.send(f"No scrim found with ID {scrim_id}.")

@client.command(name="dltorny")
async def delete_tournament_command(ctx, tournament_id: int):
    if tournament_id in registration_settings:
        await delete_tournament(ctx.guild, tournament_id)
        await ctx.send(f"Tournament with Category ID {tournament_id} has been deleted.")
    else:
        await ctx.send(f"No tournament found with Category ID {tournament_id}.")

async def start_scrim(scrim_id):
    scrim = scrims[scrim_id]
    channel = client.get_channel(scrim["channel"])  # Retrieve the channel object
    role_to_mention = client.get_guild(channel.guild.id).get_role(scrims_registration_settings[scrim["category_id"]]["ping_role"].id)  # Retrieve the role object
    await channel.send(f"{role_to_mention.mention}, Scrim '{scrim['scrim_name']}' is starting now!")
    await auto_clean_registration_channel(channel)

async def stop_scrim(scrim_id):
    scrim = scrims[scrim_id]
    channel = client.get_channel(scrim["channel"])  # Retrieve the channel object
    await channel.send(f"Scrim '{scrim['scrim_name']}' has been forcefully stopped.")


async def delete_scrim(scrim_id):
    scrim = scrims.pop(scrim_id, None)
    if scrim:
        channel = client.get_channel(scrim["channel"])  # Retrieve the channel object
        if channel:
            await channel.delete()
        role = discord.utils.get(client.get_guild(channel.guild.id).roles, id=scrim["role"])
        if role:
            await role.delete()
        save_scrims()  # Save changes
        # Optional: Remove from any related structures
        await client.get_channel(scrim["channel"].id).send(f"Scrim '{scrim['scrim_name']}' has been deleted.")

async def delete_tournament(guild: discord.Guild, tournament_id: int):
    # Get the category associated with the tournament ID
    category = discord.utils.get(guild.categories, id=tournament_id)
    if category:
        # Delete all channels within the category
        for channel in category.channels:
            await channel.delete()
        
        # Delete all roles associated with the tournament
        roles_to_delete = []
        for scrim_id, scrim_data in scrims.items():
            if scrim_data["category_id"] == tournament_id:
                role = discord.utils.get(guild.roles, id=scrim_data["role"])
                if role:
                    roles_to_delete.append(role)
        
        for role in roles_to_delete:
            await role.delete()

        # Clean up scrims and registration settings associated with the tournament
        scrims_to_delete = [sid for sid, scrim in scrims.items() if scrim["category_id"] == tournament_id]
        for scrim_id in scrims_to_delete:
            scrims.pop(scrim_id)

        tournaments.pop(tournament_id, None)

        # Delete the category itself
        await category.delete()

        # Save the updated data to the JSON files
        save_tournaments()

async def auto_clean_registration_channel(channel):
    await channel.send("This channel will be cleaned automatically in 12 hours.")
    await discord.utils.sleep_until(datetime.now() + timedelta(hours=12))
    await channel.purge()

def generate_scrim_id(length=6):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))


@client.command()
@commands.has_permissions(administrator=True)
async def clear(ctx, amount: int): #clean commmand
    if amount > 99:
        amount = 99
    deleted = await ctx.channel.purge(limit=amount)
    await ctx.send(f'Deleted {len(deleted)} message(s)', delete_after=5)

# help command
client.remove_command('help')
@client.command(name="help")
@commands.has_permissions(administrator=True)
async def help_command(ctx):
    embed = discord.Embed(
        title="Proxima Help Menu",
        description="Hello! I'm Proxima, Your Bot For Scrims and Tournament managment.",
        color= (0xC45AEC)
    )
    embed.add_field(name="Prefix For This Server", value="!", inline=False)

    
    embed.add_field(name="Main Modules", value="""
    `⚔️`Scrims
    `🏆`Tournament
    `🛠️`Clean
    """, inline=False)
    embed.add_field(name="commands", value="""         
    `⚙️`!setup ➜to setup primary channels.
    `⚙️`!tsetup ➜to set up tournament.
    `⚙️`!sttorny ➜to start tornament.
    `⚙️`!sptorny ➜to stop tornament.
    `⚙️`!dltorny ➜to delete tournament.               
    `⚙️`!ssetup ➜to set up scrims.
    `⚙️`!stscrim ➜to start scrims.
    `⚙️`!spscrim ➜to stop scrims.                
    `⚙️`!dlscrims ➜to delete scrims.
    `⚙️`!Clear [amount] ➜to clean message in any channel.                                                  
    """, inline=False)

    embed.add_field(name="Up-Coming Modules", value="""
    `📊` Points Table
    `📥` Embed
    `📀` Music
    """, inline=False)
    
    embed.add_field(name="Links", value="[Invite](https://example.com/invite) | [Support](https://discord.gg/7ZzZZFBUnY) | [Website](http://ximabot.unaux.com/)", inline=False)
    
    # Get the current time
    now = datetime.now().strftime("%Y-%m-%d at %I:%M %p")

    # Footer with dynamic author info
    embed.set_footer(text=f"Made By steg_crazy | Today at {now}")

    await ctx.send(embed=embed)

client.run(APIBOT)