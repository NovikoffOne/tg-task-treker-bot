"""
Базовые команды: /start, /help, /menu
"""
from telegram import Update
from telegram.ext import ContextTypes
from utils.keyboards import main_menu_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start с улучшенным UI"""
    user_name = update.effective_user.first_name or "Пользователь"
    
    welcome_text = (
        f"👋 <b>Привет, {user_name}!</b>\n\n"
        f"Я <b>Advanced Telegram Task Tracker Bot</b> 🤖\n\n"
        f"<b>Что я умею:</b>\n"
        f"✅ Создавать пространства и доски\n"
        f"✅ Управлять проектами с автоматическими задачами\n"
        f"✅ Синхронизировать поля между задачами проекта\n"
        f"✅ Отслеживать прогресс через дашборды\n"
        f"✅ Использовать приоритеты, метки и динамические поля\n\n"
        f"<b>Используйте меню ниже или команду</b> <code>/help</code> <b>для справки</b> 📚"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = (
        "📚 Справка по командам:\n\n"
        "🏠 Базовые:\n"
        "/start - Начать работу\n"
        "/help - Показать справку\n"
        "/menu - Главное меню\n\n"
        "📁 Пространства:\n"
        "/workspaces - Список пространств\n"
        "/newworkspace <name> - Создать пространство\n"
        "/delworkspace <name> - Удалить пространство\n"
        "/renameworkspace <old> <new> - Переименовать\n\n"
        "📋 Доски:\n"
        "/boards - Список досок\n"
        "/newboard <name> - Создать доску\n"
        "/delboard <name> - Удалить доску\n"
        "/board <name> - Показать доску\n\n"
        "📊 Проекты:\n"
        "/projects - Список проектов\n"
        "/newproject <id> <name> - Создать проект\n"
        "/project <id> - Показать проект\n"
        "/projectdashboard <id> - Дашборд проекта\n\n"
        "📝 Задачи:\n"
        "/newtask - Создать задачу\n"
        "/task <id> - Показать задачу\n"
        "/movetask <id> <column> - Переместить задачу\n"
        "/priority <id> <level> - Установить приоритет\n\n"
        "📈 Статистика:\n"
        "/stats - Общая статистика\n"
        "/statsproject <id> - Статистика проекта\n"
    )
    
    await update.message.reply_text(help_text)

async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /menu"""
    await update.message.reply_text(
        "🏠 Главное меню",
        reply_markup=main_menu_keyboard()
    )

async def test_handlers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Простая команда для проверки работы обработчиков"""
    await update.message.reply_text(
        "✅ Обработчики работают!\n\n"
        "Попробуйте команду: /start_test_basecase"
    )

async def start_test_basecase_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды @start_test_baseCase - запуск базового теста"""
    import logging
    import asyncio
    import traceback
    
    logger = logging.getLogger(__name__)
    logger.info("="*60)
    logger.info("КОМАНДА start_test_basecase ПОЛУЧЕНА!")
    logger.info(f"Update: {update}")
    logger.info(f"Message: {update.message}")
    logger.info("="*60)
    
    user_id = update.effective_user.id
    
    # Сразу отправляем подтверждение, что команда получена
    await update.message.reply_text("✅ Команда получена! Начинаю тест...")
    
    try:
        await update.message.reply_text(
            "🚀 Запуск базового теста...\n\n"
            "Это может занять некоторое время. Пожалуйста, подождите..."
        )
        
        logger.info(f"Импорт модулей для пользователя {user_id}")
        
        # Импорты внутри функции для избежания проблем с путями
        import sys
        import os
        
        # Добавляем путь к корню проекта
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from database import Database
        from tests.test_base_case import BaseCaseTestRunner
        
        logger.info("Модули импортированы, создаем БД и runner")
        
        db = Database()
        db.init_db()
        runner = BaseCaseTestRunner(db, user_id)
        
        logger.info("Запуск теста в отдельном потоке")
        
        # Запуск теста в отдельном потоке, чтобы не блокировать бота
        success = await asyncio.to_thread(runner.run_test)
        
        logger.info(f"Тест завершен, success={success}")
        
        if success:
            # Подготовить отчет
            passed = sum(1 for r in runner.test_results if r["status"] == "PASSED")
            failed = sum(1 for r in runner.test_results if r["status"] == "FAILED")
            total = len(runner.test_results)
            
            report = (
                f"✅ <b>Базовый тест завершен!</b>\n\n"
                f"📊 <b>Результаты:</b>\n"
                f"Всего шагов: {total}\n"
                f"✅ Пройдено: {passed}\n"
                f"❌ Провалено: {failed}\n\n"
            )
            
            if failed == 0:
                report += "🎉 <b>Все тесты пройдены успешно!</b>"
            else:
                report += "⚠️ <b>Некоторые тесты провалены. Проверьте логи.</b>\n\n"
                report += "<b>Проваленные шаги:</b>\n"
                for result in runner.test_results:
                    if result["status"] == "FAILED":
                        report += f"❌ {result['step']}: {result['message']}\n"
            
            await update.message.reply_text(report, parse_mode='HTML')
        else:
            await update.message.reply_text(
                "❌ <b>Тест провален</b>\n\n"
                "Проверьте логи для деталей.",
                parse_mode='HTML'
            )
    except ImportError as e:
        error_msg = f"Ошибка импорта: {str(e)}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        await update.message.reply_text(
            f"❌ <b>Ошибка импорта модулей:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Проверьте логи бота.",
            parse_mode='HTML'
        )
    except Exception as e:
        error_msg = f"Ошибка при запуске теста: {str(e)}\n\n{traceback.format_exc()}"
        logger.error(error_msg)
        await update.message.reply_text(
            f"❌ <b>Ошибка при запуске теста:</b>\n\n"
            f"<code>{str(e)}</code>\n\n"
            f"Проверьте логи бота для деталей.",
            parse_mode='HTML'
        )

