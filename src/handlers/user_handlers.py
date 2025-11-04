from aiogram import Router, F
from aiogram.filters import CommandStart, Command, StateFilter 
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker 
from sqlalchemy import select, func
from src.middlewares.admin_check import AdminMiddleware
from src.database.models import User, PortfolioItem, Category 
from src.fsm.project_fsm import AddProjectStates, UserAddProjectStates 
from src.callbacks.project_cb import ProjectCallback, CategoryCallback
from src.config import settings

router = Router()
admin_router = Router()
admin_router.message.middleware(AdminMiddleware()) 

# --- PRIVATE KEYBOARD FUNCTIONS AND UTILITIES ---

def get_help_keyboard() -> InlineKeyboardMarkup:
    """Returns the keyboard for the /help command."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Suggest a Project", callback_data="start_user_add_project")],
        [InlineKeyboardButton(text="💼 My Portfolio", callback_data="show_portfolio")]
    ])

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Returns the main admin panel keyboard, including public buttons."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚨 Project Moderation", callback_data="admin_moderate_list")],
        [InlineKeyboardButton(text="➕ Add Project (as Admin)", callback_data="admin_add_project")],
        [InlineKeyboardButton(text="📊 User Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👤 User List", callback_data="admin_list_users")],
        [InlineKeyboardButton(text="💼 View Portfolio", callback_data="show_portfolio")]
    ])

async def get_categories_keyboard(session: AsyncSession) -> InlineKeyboardMarkup:
    """Returns the keyboard for category selection."""
    categories_stmt = select(Category).order_by(Category.name)
    categories = await session.scalars(categories_stmt)
    
    buttons = []
    
    # "All Categories" button
    buttons.append([InlineKeyboardButton(
        text="⭐️ ALL PROJECTS", 
        callback_data=CategoryCallback(category_id=0).pack()
    )])
    
    # Category buttons
    row = []
    for cat in categories:
        row.append(InlineKeyboardButton(
            text=cat.name, 
            callback_data=CategoryCallback(category_id=cat.id).pack()
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="show_start")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_project_navigation_keyboard(item: PortfolioItem, total_count: int, current_index: int, category_id: int, is_admin: bool = False, is_moderator_view: bool = False) -> InlineKeyboardMarkup:
    """Returns the keyboard for project navigation."""
    buttons = []
    
    # Navigation buttons (Back/Next)
    nav_row = []
    if current_index > 0:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Back", 
            callback_data=ProjectCallback(action="prev", item_id=item.id, current_index=current_index, category_id=category_id).pack()
        ))
    
    nav_row.append(InlineKeyboardButton(text=f"{current_index + 1}/{total_count}", callback_data="ignore"))
    
    if current_index < total_count - 1:
        nav_row.append(InlineKeyboardButton(
            text="Next ➡️", 
            callback_data=ProjectCallback(action="next", item_id=item.id, current_index=current_index, category_id=category_id).pack()
        ))
    buttons.append(nav_row)

    # Action buttons (Link, Delete)
    action_row = []
    # Strict check for URL correctness
    link_valid = item.link and (item.link.startswith("http://") or item.link.startswith("https://"))
    
    if link_valid:
        action_row.append(InlineKeyboardButton(text="🔗 Go to Project", url=item.link))

    # --- CHANGE: Add "Download Document" button ---
    if item.document_file_id:
        action_row.append(InlineKeyboardButton(
            text="📄 Download Document", 
            callback_data=ProjectCallback(
                action="get_doc", # New action
                item_id=item.id, 
                current_index=current_index, 
                category_id=category_id
            ).pack()
        ))
    # --- END OF CHANGE ---

    if is_admin and not is_moderator_view:
         action_row.append(InlineKeyboardButton(
             text="🗑️ Delete Project", 
             callback_data=ProjectCallback(action="delete", item_id=item.id, current_index=current_index, category_id=category_id).pack()
         ))
    
    buttons.append(action_row)
    
    # Back button
    if is_moderator_view:
         buttons.append([InlineKeyboardButton(text="🔙 Back to Moderation Menu", callback_data="back_to_admin_main_menu")])
    else:
        buttons.append([InlineKeyboardButton(text="🗂️ To Categories", callback_data="show_categories")])
        buttons.append([InlineKeyboardButton(text="🔙 Back to Main Menu", callback_data="show_start")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- Public Handlers (router) ---

@router.message(CommandStart())
async def command_start_handler(message: Message, session_maker: async_sessionmaker[AsyncSession]):
    
    # --- ENSURE USER CREATION ---
    user_id = message.from_user.id
    username = message.from_user.username
    
    async with session_maker() as session:
        user_stmt = select(User).where(User.user_id == user_id)
        user = await session.scalar(user_stmt)
        
        if not user:
            new_user = User(
                user_id=user_id,
                username=username,
                is_admin=(user_id == settings.ADMIN_ID)
            )
            session.add(new_user)
            await session.commit()
        elif user.username != username:
            user.username = username
            await session.commit()
    # -----------------------------------------------------------------

    await message.answer(
        f"👋 Hi, {message.from_user.full_name}! I am a portfolio bot created with Python.\n"
        "How can I help you? Use /help to see all commands.",
        reply_markup=get_help_keyboard(),
        parse_mode='HTML'
    )

@router.message(Command("help"))
async def command_help_handler(message: Message):
    """Displays the list of available commands and the main menu."""
    await message.answer(
        "I can execute the following commands:\n"
        "• /start — Start communication\n"
        "• /help — Show this menu\n"
        "• /add_project — Suggest your project\n"
        "\nUse the buttons for quick access:",
        reply_markup=get_help_keyboard(),
        parse_mode='HTML'
    )

# --- PUBLIC MENU BUTTON HANDLERS (CALLBACKS) ---

@router.callback_query(F.data == "show_start")
async def callback_show_start(callback: CallbackQuery, state: FSMContext): # <--- 1. ДОБАВЛЕНО: state: FSMContext
    """Handler for the 'Start Over/Back to Main Menu' button."""
    
    if callback.message.text and callback.message.text.startswith("👋 Hi,"):
        await callback.answer("You are already in the main menu!", show_alert=False)
        return
        
    await callback.answer()
    
    # 2. КЛЮЧЕВОЕ ИСПРАВЛЕНИЕ: Сброс FSM-состояния
    await state.clear() 
    
    # DELETE the old message and SEND a new one (safe method)
    try:
        await callback.message.delete()
    except Exception:
        pass
    
    await callback.message.answer(
        f"👋 Hi, {callback.from_user.full_name}! How can I help you?",
        reply_markup=get_help_keyboard(),
        parse_mode='HTML'
    )

# --- Handler: Category Selection ---
@router.callback_query(F.data == "show_portfolio", StateFilter(None))
@router.callback_query(F.data == "show_categories", StateFilter(None))
async def show_categories_handler(callback: CallbackQuery, session_maker: async_sessionmaker[AsyncSession]):
    """Shows the category selection menu."""
    await callback.answer()
    
    async with session_maker() as session:
        keyboard = await get_categories_keyboard(session)
    
    # Check to avoid editing a photo as text
    if callback.message.photo:
         try: await callback.message.delete() 
         except: pass
         await callback.message.answer(
             "🗂️ PORTFOLIO: Select a category to view projects:",
             reply_markup=keyboard,
             parse_mode='HTML'
         )
    else:
        await callback.message.edit_text(
            "🗂️ PORTFOLIO: Select a category to view projects:",
            reply_markup=keyboard,
            parse_mode='HTML'
        )

# --- Handler: Display projects by category and navigation ---
@router.callback_query(CategoryCallback.filter(), StateFilter(None))
@router.callback_query(ProjectCallback.filter(F.action.in_({"next", "prev"})), StateFilter(None))
async def show_portfolio_by_category_handler(callback: CallbackQuery, session_maker: async_sessionmaker[AsyncSession]):
    """Handler for displaying and navigating projects within the selected category."""
    
    is_admin = callback.from_user.id == settings.ADMIN_ID 
    current_index = 0
    
    # --- FIX for 'AttributeError' ---
    if callback.data.startswith('cat'):
        # If it's a CategoryCallback (category selection)
        callback_data = CategoryCallback.unpack(callback.data)
        category_id = callback_data.category_id
        current_index = 0
    else:
        # If it's a ProjectCallback (next/prev)
        callback_data = ProjectCallback.unpack(callback.data)
        category_id = callback_data.category_id
        
        if callback_data.action == "next":
            current_index = callback_data.current_index + 1
        else: # action == "prev"
            current_index = callback_data.current_index - 1
    # ----------------------------------------------------

    async with session_maker() as session:
        # Build query: select only APPROVED projects
        stmt = select(PortfolioItem).where(PortfolioItem.is_approved == True)
        if category_id != 0:
            stmt = stmt.where(PortfolioItem.category_id == category_id)
        
        # Get the total count
        total_count_stmt = select(func.count(PortfolioItem.id)).where(PortfolioItem.is_approved == True)
        if category_id != 0:
            total_count_stmt = total_count_stmt.where(PortfolioItem.category_id == category_id)
            
        total_count = await session.scalar(total_count_stmt)

        if total_count == 0:
            await callback.answer("There are no approved projects in this category yet 😟")
            # Return to categories
            await show_categories_handler(callback, session_maker)
            return

        # Get the project object by index
        stmt = stmt.limit(1).offset(current_index).order_by(PortfolioItem.id)
        item = await session.scalar(stmt)
        
        category_name = "All Projects"
        if category_id != 0:
             cat = await session.get(Category, category_id)
             if cat: category_name = cat.name
             
    caption = (
        f"🗂️ Category: {category_name}\n"
        f"💼 PROJECT ({current_index + 1}/{total_count}): {item.title}\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"*{item.description}*"
    )
    
    # Pass category_id to the keyboard to maintain context
    keyboard = get_project_navigation_keyboard(item, total_count, current_index, category_id, is_admin)
    
    await callback.answer()
    
    # --- CHANGE: `item.telegram_file_id` -> `item.photo_file_id` ---
    if item.photo_file_id:
        try:
            # Try to delete the previous message to send a photo
            await callback.message.delete()
        except Exception:
            pass 
            
        await callback.message.answer_photo(
            photo=item.photo_file_id, # --- CHANGE ---
            caption=caption, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )
    else:
        await callback.message.edit_text(
            caption, 
            reply_markup=keyboard, 
            parse_mode='Markdown'
        )

# --- NEW HANDLER: Send document via button ---
@router.callback_query(ProjectCallback.filter(F.action == "get_doc"), StateFilter(None))
async def send_project_document_handler(callback: CallbackQuery, callback_data: ProjectCallback, session_maker: async_sessionmaker[AsyncSession]):
    """Sends the document attached to the project."""
    await callback.answer("Loading document...")
    
    async with session_maker() as session:
        item = await session.get(PortfolioItem, callback_data.item_id)
        
        if item and item.document_file_id:
            try:
                # Send as a new message
                await callback.message.answer_document(item.document_file_id)
            except Exception as e:
                await callback.answer(f"⛔️ Error sending file: {e}", show_alert=True)
        else:
            await callback.answer("⛔️ Document not found or was deleted.", show_alert=True)

# --- FSM FOR USER (PUBLIC ACCESS) ---

@router.message(Command("add_project"), StateFilter(None))
@router.callback_query(F.data == "start_user_add_project", StateFilter(None)) 
async def command_add_project_handler(union: Message | CallbackQuery, state: FSMContext, session_maker: async_sessionmaker[AsyncSession]):
    """Start FSM: Ask for category."""
    
    message_to_edit = union.message if isinstance(union, CallbackQuery) else union
    
    async with session_maker() as session:
        keyboard = await get_categories_keyboard(session)
        
    # --- CHANGE: Step 1/6 ---
    step_text = "➡️ SUGGESTING YOUR PROJECT\n\n" \
                "Step 1/6: Select the project category:"
    
    if isinstance(union, CallbackQuery):
        await union.answer()
        # Check that the message is not a photo before editing text
        if union.message.photo:
            try: await union.message.delete()
            except: pass
            
            await message_to_edit.answer(
                step_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
        else:
             await union.message.edit_text(
                step_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
    else:
        await message_to_edit.answer(
            step_text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )
        
    await state.set_state(UserAddProjectStates.get_category)

@router.callback_query(UserAddProjectStates.get_category, CategoryCallback.filter())
async def user_process_project_category(callback: CallbackQuery, callback_data: CategoryCallback, state: FSMContext):
    """Get category and ask for title."""
    
    # FIX: Disallow selecting "All Projects" when adding
    if callback_data.category_id == 0:
         await callback.answer("Please select a specific category for your project.", show_alert=True)
         return

    await callback.answer()
    await state.update_data(category_id=callback_data.category_id)
    
    # --- CHANGE: Step 2/6 ---
    await callback.message.edit_text(
        "Step 2/6: Enter the project title:", 
        reply_markup=None, 
        parse_mode='HTML'
    )
    await state.set_state(UserAddProjectStates.get_title)

@router.message(UserAddProjectStates.get_title, F.text)
async def user_process_project_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    # --- CHANGE: Step 3/6 ---
    await message.answer("Step 3/6: Enter a detailed description of the project:", parse_mode='HTML')
    await state.set_state(UserAddProjectStates.get_description)

@router.message(UserAddProjectStates.get_description, F.text)
async def user_process_project_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    # --- CHANGE: Step 4/6 ---
    await message.answer("Step 4/6: Enter the project link (or type 'no'):", parse_mode='HTML')
    await state.set_state(UserAddProjectStates.get_link)

@router.message(UserAddProjectStates.get_link, F.text) # --- CHANGE: F.text ---
async def user_process_project_link(message: Message, state: FSMContext):
    link = message.text if message.text and message.text.lower() != 'no' else None
    await state.update_data(link=link)
    # --- CHANGE: Step 5/6 and new text ---
    await message.answer("Step 5/6: Send a photo (cover) for this project (or type 'no'):", parse_mode='HTML')
    await state.set_state(UserAddProjectStates.get_photo)

@router.message(UserAddProjectStates.get_photo, F.photo | F.text) # --- CHANGE: F.photo | F.text ---
async def user_process_project_photo(message: Message, state: FSMContext):
    
    # --- CHANGE: New logic for photo ---
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id 
    elif message.text and message.text.lower() == 'no':
        pass # photo_file_id is already None
    else:
        await message.answer("Invalid format. Please send a photo or type 'no'.")
        return

    await state.update_data(photo_file_id=photo_file_id)
    
    # --- CHANGE: Proceed to Step 6/6 ---
    await message.answer("Step 6/6: Great. Now, if needed, send a document (PDF, ZIP, etc.) or type 'no':", parse_mode='HTML')
    await state.set_state(UserAddProjectStates.get_document)

# --- NEW HANDLER: Step 6 - Get Document ---
@router.message(UserAddProjectStates.get_document, F.document | F.text)
async def user_process_project_document(message: Message, state: FSMContext, session_maker: async_sessionmaker[AsyncSession]):
    
    doc_file_id = None
    if message.document:
        doc_file_id = message.document.file_id
    elif message.text and message.text.lower() == 'no':
        pass # doc_file_id is already None
    else:
        await message.answer("Invalid format. Please send a document or type 'no'.")
        return

    data = await state.get_data()
    
    # * KEY POINT: is_approved=False *
    new_item = PortfolioItem(
        title=data['title'],
        description=data['description'],
        link=data['link'],
        photo_file_id=data['photo_file_id'], # --- CHANGE ---
        document_file_id=doc_file_id,       # --- NEW ---
        user_id=message.from_user.id, 
        category_id=data['category_id'], 
        is_approved=False # Project is NOT APPROVED by default
    )

    async with session_maker() as session:
        session.add(new_item)
        await session.commit()

    # * KEY POINT: Moderation message *
    await message.answer(
        f"✅ Your project '{data['title']}' has been sent for moderation! An administrator will review it soon.",
        reply_markup=get_help_keyboard(),
        parse_mode='HTML'
    )
    await state.clear()

# --- NEW HANDLER: Error at Step 6 ---
@router.message(UserAddProjectStates.get_document)
async def user_process_project_document_invalid(message: Message):
    await message.answer("Invalid format. Please send a document or type 'no'.")

# --- CHANGE: Error text ---
@router.message(UserAddProjectStates.get_photo)
async def user_process_project_photo_invalid(message: Message):
    await message.answer("Invalid format. Please send a photo or type 'no'.")

# !!! THIS HANDLER MUST BE THE LAST ONE IN 'router' !!!
@router.message()
async def echo_handler(message: Message):
    """Catches all messages that didn't match the commands above."""
    await message.answer(
        "Sorry, I don't understand this command. 😕\n"
        "Try /help for a list of commands."
    )

# --- Admin Handlers (admin_router) ---

@admin_router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    """Entry to admin panel (checked by middleware)."""
    await message.answer(
        "🔐 <b>Admin Panel:</b> Select an action.", 
        reply_markup=get_admin_main_keyboard(), 
        parse_mode='HTML'
    )

# --- 1. STATISTICS LOGIC ---

@admin_router.callback_query(F.data.in_({'admin_stats', 'admin_list_users'}))
async def admin_stats_handler(callback: CallbackQuery, session_maker: async_sessionmaker[AsyncSession]): 
    """Displays detailed statistics on users and projects."""
    
    await callback.answer("Gathering statistics...")
    
    async with session_maker() as session:
        total_users_stmt = select(func.count(User.id))
        total_users = await session.scalar(total_users_stmt)
        
        total_projects_stmt = select(func.count(PortfolioItem.id))
        total_projects = await session.scalar(total_projects_stmt)
        
        # Count approved projects
        approved_projects_stmt = select(func.count(PortfolioItem.id)).where(PortfolioItem.is_approved == True)
        approved_projects = await session.scalar(approved_projects_stmt)
        
        pending_projects = total_projects - approved_projects

        if callback.data == 'admin_list_users':
            user_list_stmt = select(User.user_id, User.username).order_by(User.id.desc()).limit(10)
            user_list_result = await session.execute(user_list_stmt)
            users_data = user_list_result.all()
            
            user_details = "\n".join(
                [f"• <code>@{u[1]}</code> (ID: <code>{u[0]}</code>)" if u[1] else f"• ID: <code>{u[0]}</code>" 
                 for u in users_data]
            )
            stats_text = (
                f"📊 BOT STATISTICS\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"• Total users: {total_users}\n"
                f"• Total projects (all): {total_projects}\n"
                f"• Approved: {approved_projects}\n"
                f"• Pending moderation: {pending_projects}\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"LAST 10 USERS:\n{user_details}"
            )
        else:
            stats_text = (
                f"📊 BOT STATISTICS\n"
                f"➖➖➖➖➖➖➖➖➖➖\n"
                f"• Total users: {total_users}\n"
                f"• Total projects (all): {total_projects}\n"
                f"• Approved: {approved_projects}\n"
                f"• Pending moderation: {pending_projects}"
            )

    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_main_keyboard(),
        parse_mode='HTML'
    )

# --- 2. ADMIN PROJECT ADDITION LOGIC (FSM) ---

@admin_router.callback_query(F.data == "back_to_admin_main_menu")
async def admin_main_menu_handler(callback: CallbackQuery):
    # ... (логика, которую вы предоставили)
    await callback.answer() 
    
    try:
        await callback.message.delete()
    except Exception:
        pass
        
    await callback.message.answer(
        "🔐 <b>Admin Panel:</b> Select an action.", 
        reply_markup=get_admin_main_keyboard(), 
        parse_mode='HTML'
    )
    
@admin_router.callback_query(AddProjectStates.get_category, CategoryCallback.filter())
async def admin_process_project_category(callback: CallbackQuery, callback_data: CategoryCallback, state: FSMContext):
    # FIX: Disallow selecting "All Projects" when adding
    if callback_data.category_id == 0:
         await callback.answer("Please select a specific category for your project.", show_alert=True)
         return

    await callback.answer()
    await state.update_data(category_id=callback_data.category_id)
    
    # --- CHANGE: Step 2/6 ---
    await callback.message.edit_text(
        "Step 2/6: Enter the project title:", 
        reply_markup=None, 
        parse_mode='HTML'
    )
    await state.set_state(AddProjectStates.get_title)

@admin_router.message(AddProjectStates.get_title, F.text)
async def admin_process_project_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    # --- CHANGE: Step 3/6 ---
    await message.answer("Step 3/6: Enter a detailed description of the project:", parse_mode='HTML')
    await state.set_state(AddProjectStates.get_description)
    
@admin_router.message(AddProjectStates.get_description, F.text)
async def admin_process_project_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    # --- CHANGE: Step 4/6 ---
    await message.answer("Step 4/6: Enter the project link (or type 'no'):", parse_mode='HTML')
    await state.set_state(AddProjectStates.get_link)
    
@admin_router.message(AddProjectStates.get_link, F.text) # --- CHANGE: F.text ---
async def admin_process_project_link(message: Message, state: FSMContext):
    link = message.text if message.text and message.text.lower() != 'no' else None
    await state.update_data(link=link)
    # --- CHANGE: Step 5/6 and new text ---
    await message.answer("Step 5/6: Send a photo (cover) for this project (or type 'no').", parse_mode='HTML')
    await state.set_state(AddProjectStates.get_photo)

@admin_router.message(AddProjectStates.get_photo, F.photo | F.text) # --- CHANGE: F.photo | F.text ---
async def admin_process_project_photo(message: Message, state: FSMContext):
    """Get photo, save to state, and ask for document (Admin)."""
    
    # --- CHANGE: New logic for photo ---
    photo_file_id = None
    if message.photo:
        photo_file_id = message.photo[-1].file_id 
    elif message.text and message.text.lower() == 'no':
        pass # photo_file_id is already None
    else:
        await message.answer("Invalid format. Please send a photo or type 'no'.")
        return

    await state.update_data(photo_file_id=photo_file_id)
    
    # --- CHANGE: Proceed to Step 6/6 ---
    await message.answer("Step 6/6: Great. Now, if needed, send a document (PDF, ZIP, etc.) or type 'no':", parse_mode='HTML')
    await state.set_state(AddProjectStates.get_document)

# --- NEW HANDLER: Step 6 - Get Document (Admin) ---
@admin_router.message(AddProjectStates.get_document, F.document | F.text)
async def admin_process_project_document(message: Message, state: FSMContext, session_maker: async_sessionmaker[AsyncSession]):
    
    doc_file_id = None
    if message.document:
        doc_file_id = message.document.file_id
    elif message.text and message.text.lower() == 'no':
        pass # doc_file_id is already None
    else:
        await message.answer("Invalid format. Please send a document or type 'no'.")
        return

    data = await state.get_data()
    
    new_item = PortfolioItem(
        title=data['title'],
        description=data['description'],
        link=data['link'],
        photo_file_id=data['photo_file_id'], # --- CHANGE ---
        document_file_id=doc_file_id,       # --- NEW ---
        user_id=message.from_user.id, 
        category_id=data['category_id'],
        is_approved=True # Admin's project is approved automatically
    )

    async with session_maker() as session:
        session.add(new_item)
        await session.commit()

    await message.answer(
        f"✅ Project '{data['title']}' successfully added to the database!",
        reply_markup=get_admin_main_keyboard(),
        parse_mode='HTML'
    )
    await state.clear()

# --- NEW HANDLER: Error at Step 6 (Admin) ---
@admin_router.message(AddProjectStates.get_document)
async def admin_process_project_document_invalid(message: Message):
    await message.answer("Invalid format. Please send a document or type 'no'.")

# --- CHANGE: Error text ---
@admin_router.message(AddProjectStates.get_photo)
async def admin_process_project_photo_invalid(message: Message):
    await message.answer("Invalid format. Please send a photo or type 'no'.")

# --- 3. PROJECT MODERATION LOGIC (ADMIN) ---

# --- NEW HANDLER: Send Document (Admin) ---
@admin_router.callback_query(ProjectCallback.filter(F.action == "get_doc"))
async def admin_send_project_document_handler(callback: CallbackQuery, callback_data: ProjectCallback, session_maker: async_sessionmaker[AsyncSession]):
    """Sends the document attached to the project (for admin)."""
    await callback.answer("Loading document...")
    
    async with session_maker() as session:
        item = await session.get(PortfolioItem, callback_data.item_id)
        
        if item and item.document_file_id:
            try:
                await callback.message.answer_document(item.document_file_id)
            except Exception as e:
                await callback.answer(f"⛔️ Error sending file: {e}", show_alert=True)
        else:
            await callback.answer("⛔️ Document not found or was deleted.", show_alert=True)

@admin_router.callback_query(F.data == "admin_moderate_list")
@admin_router.callback_query(ProjectCallback.filter(F.action.in_({"next", "prev"})))
async def admin_moderate_list_handler(callback: CallbackQuery, session_maker: async_sessionmaker[AsyncSession], callback_data=None):
    """Shows the list of projects awaiting moderation."""
    
    is_admin = callback.from_user.id == settings.ADMIN_ID 
    current_index = 0
    
    if callback.data != "admin_moderate_list":
        # If it's a ProjectCallback (next/prev)
        callback_data = ProjectCallback.unpack(callback.data)
        if callback_data.action == "next":
            current_index = callback_data.current_index + 1
        else: # action == "prev"
            current_index = callback_data.current_index - 1
        
    async with session_maker() as session:
        # * KEY POINT: Select only NON-APPROVED projects *
        stmt = select(PortfolioItem).where(PortfolioItem.is_approved == False)
        
        total_count_stmt = select(func.count(PortfolioItem.id)).where(PortfolioItem.is_approved == False)
        total_count = await session.scalar(total_count_stmt)

        if total_count == 0:
            await callback.answer("✅ No new projects pending moderation.", show_alert=True)
          
            # ИСПРАВЛЕНИЕ: Вместо сложного редактирования используем удаление и новую отправку
            try:
                await callback.message.delete()
            except Exception:
                pass
            
            await callback.message.answer(
                "🔐 <b>Admin Panel:</b> Select an action.", 
                reply_markup=get_admin_main_keyboard(), 
                parse_mode='HTML'
            )
            return

        # Get the project object
        stmt = stmt.limit(1).offset(current_index).order_by(PortfolioItem.id)
        item = await session.scalar(stmt)
        
        category_name = await session.scalar(select(Category.name).where(Category.id == item.category_id))
        
    # Format the message for moderation
    caption = (
        f"🚨 MODERATION ({current_index + 1}/{total_count}):\n"
        f"🗂️ Category: {category_name}\n"
        f"📝 Title: {item.title}\n"
        f"👤 Added by: <code>{item.user_id}</code>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"*{item.description}*"
    )
    
    # Navigation keyboard
    keyboard = get_project_navigation_keyboard(
        item=item, 
        total_count=total_count, 
        current_index=current_index, 
        category_id=0,
        is_admin=is_admin,
        is_moderator_view=True # Use the moderation keyboard layout
    )
    
    moderate_row = [
            InlineKeyboardButton(
                text="✅ APPROVE", 
                callback_data=ProjectCallback(action="approve", item_id=item.id, current_index=current_index, category_id=0).pack()
            ),
            InlineKeyboardButton(
                text="❌ REJECT", 
                callback_data=ProjectCallback(action="reject", item_id=item.id, current_index=current_index, category_id=0).pack()
            )
        ]
        # Insert moderation buttons BEFORE the back button
    keyboard.inline_keyboard.insert(-1, moderate_row)
        
    await callback.answer()
        
        # --- CHANGE: `item.telegram_file_id` -> `item.photo_file_id` ---
    if item.photo_file_id:
            try:
                await callback.message.delete()
            except Exception:
                pass 
                
            await callback.message.answer_photo(
                photo=item.photo_file_id, 
                caption=caption, 
                reply_markup=keyboard, 
                parse_mode='Markdown'
            )
    else:
            await callback.message.edit_text(
                caption, 
                reply_markup=keyboard, 
                parse_mode='Markdown'
            )

# --- NEW HANDLER: Approve Project ---
@admin_router.callback_query(ProjectCallback.filter(F.action == "approve"))
async def admin_approve_project_handler(callback: CallbackQuery, callback_data: ProjectCallback, session_maker: async_sessionmaker[AsyncSession]):
    """Approves the project and notifies the user."""
    
    async with session_maker() as session:
        item = await session.get(PortfolioItem, callback_data.item_id)
        
        if not item:
            await callback.answer("⛔️ Project not found (perhaps deleted).", show_alert=True)
            return
        
        if item.is_approved:
            await callback.answer("✅ This project has already been approved.", show_alert=True)
            return

        item.is_approved = True
        await session.commit()
        
        await callback.answer(f"✅ Project '{item.title}' APPROVED!", show_alert=True)
        
        # Notify the user
        try:
            await callback.bot.send_message(
                chat_id=item.user_id,
                text=f"🎉 Congratulations! Your project '{item.title}' has passed moderation and been added to the portfolio!",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Failed to notify user {item.user_id}: {e}")

    # Refresh the moderation message (return to the list)
    await admin_moderate_list_handler(callback, session_maker, callback_data)

# --- NEW HANDLER: Reject Project ---
@admin_router.callback_query(ProjectCallback.filter(F.action == "reject"))
async def admin_reject_project_handler(callback: CallbackQuery, callback_data: ProjectCallback, session_maker: async_sessionmaker[AsyncSession]):
    """Rejects (deletes) the project and notifies the user."""
    
    async with session_maker() as session:
        item = await session.get(PortfolioItem, callback_data.item_id)
        
        if not item:
            await callback.answer("⛔️ Project not found (perhaps already deleted).", show_alert=True)
            return

        title_for_notification = item.title
        user_id_for_notification = item.user_id
        
        await session.delete(item)
        await session.commit()
        
        await callback.answer(f"❌ Project '{title_for_notification}' REJECTED and DELETED.", show_alert=True)

        try:
            await callback.bot.send_message(
                chat_id=user_id_for_notification,
                text=f"❌ Unfortunately, your project '{title_for_notification}' was rejected by the moderator.",
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Failed to notify user {user_id_for_notification}: {e}")

    await admin_moderate_list_handler(callback, session_maker, callback_data)

@admin_router.callback_query(ProjectCallback.filter(F.action == "delete"))
async def admin_delete_project_handler(callback: CallbackQuery, callback_data: ProjectCallback, session_maker: async_sessionmaker[AsyncSession]):
    """Deletes a project (for admin, from the general list)."""
    
    async with session_maker() as session:
        item = await session.get(PortfolioItem, callback_data.item_id)
        
        if not item:
            await callback.answer("⛔️ Project already deleted.", show_alert=True)
            return

        title = item.title
        await session.delete(item)
        await session.commit()
        
        await callback.answer(f"✅ Project '{title}' deleted.", show_alert=True)
        
        await show_categories_handler(callback, session_maker)