"""
AI Handler для обработки естественных запросов через систему агентов
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from agents.agent_coordinator import AgentCoordinator
from database import Database
from repositories.workspace_repository import WorkspaceRepository

logger = logging.getLogger(__name__)

# Глобальный экземпляр координатора (инициализируется при первом использовании)
_agent_coordinator = None


def get_agent_coordinator() -> AgentCoordinator:
    """Получить или создать экземпляр AgentCoordinator"""
    global _agent_coordinator
    if _agent_coordinator is None:
        db = Database()
        _agent_coordinator = AgentCoordinator(db=db)
        logger.info("AgentCoordinator создан")
    return _agent_coordinator


def get_user_workspace(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Получить workspace пользователя из user_data или БД
    
    Args:
        user_id: ID пользователя
        context: Контекст Telegram бота
        
    Returns:
        ID workspace пользователя
        
    Raises:
        ValueError: Если у пользователя нет workspace
    """
    # Проверяем сохраненный workspace в user_data
    if context.user_data and 'current_workspace_id' in context.user_data:
        workspace_id = context.user_data['current_workspace_id']
        logger.debug(f"Использован сохраненный workspace {workspace_id} для пользователя {user_id}")
        return workspace_id
    
    # Если workspace не сохранен, получаем из БД
    db = Database()
    workspace_repo = WorkspaceRepository(db)
    workspaces = workspace_repo.get_all_by_user(user_id)
    
    if not workspaces:
        raise ValueError("У пользователя нет пространств")
    
    # Используем первое пространство и сохраняем в user_data
    workspace_id = workspaces[0].id
    if context.user_data is None:
        context.user_data = {}
    context.user_data['current_workspace_id'] = workspace_id
    logger.info(f"Workspace {workspace_id} сохранен в user_data для пользователя {user_id}")
    
    return workspace_id


async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /ai для активации AI-режима
    
    Показывает инструкции по использованию AI-режима
    """
    message = """🤖 AI-режим активирован!

Теперь вы можете писать запросы естественным языком, например:
• "Создай новый проект id+ Polaroid Photo"
• "Добавь ссылку ТЗ к проекту 5005"
• "Закрой задачу на доске Подготовка"
• "Сколько задач в работе?"

Просто напишите ваш запрос, и я обработаю его через AI-агентов.

Для выхода из AI-режима используйте команду /menu"""
    
    await update.message.reply_text(message)


async def handle_ai_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Обработчик естественных запросов пользователя
    
    Определяет, является ли сообщение естественным запросом (не командой)
    и обрабатывает его через AgentCoordinator
    """
    import time
    start_time = time.time()
    
    # Логирование входа в обработчик
    logger.info(f"handle_ai_message вызван: update.message={update.message is not None}, text={update.message.text if update.message else None}")
    
    if not update.message or not update.message.text:
        logger.debug("handle_ai_message: пропущено (нет сообщения или текста)")
        return
    
    text = update.message.text.strip()
    user_id = update.effective_user.id
    
    logger.info(f"Обработка AI-запроса для user_id={user_id}, message='{text[:100]}...'")
    
    # Пропускаем команды (начинаются с /)
    if text.startswith('/'):
        logger.debug(f"Пропущено сообщение (команда): {text[:50]}")
        return
    
    # Пропускаем очень короткие сообщения (вероятно, не запросы)
    if len(text) < 5:
        logger.debug(f"Пропущено сообщение (слишком короткое): {text}")
        return
    
    try:
        # Получить workspace пользователя из user_data или БД
        try:
            workspace_id = get_user_workspace(user_id, context)
            logger.debug(f"Workspace_id={workspace_id} для user_id={user_id}")
        except ValueError as e:
            logger.warning(f"У пользователя {user_id} нет workspace")
            await update.message.reply_text(
                f"❌ {str(e)}. Создайте пространство командой /newworkspace"
            )
            return
        
        # Показать индикатор обработки
        processing_msg = await update.message.reply_text("🤔 Обрабатываю запрос...")
        
        # Получить координатор агентов
        coordinator = get_agent_coordinator()
        
        # Обработать запрос через систему агентов
        logger.debug(f"Отправка запроса в AgentCoordinator: '{text[:100]}...'")
        result = coordinator.process_user_message(
            user_message=text,
            workspace_id=workspace_id,
            user_id=user_id
        )
        
        elapsed_time = time.time() - start_time
        status = result.get('status', 'unknown')
        
        # Логирование результатов обработки
        logger.info(
            f"AI запрос обработан за {elapsed_time:.2f}s: "
            f"user_id={user_id}, status={status}, message='{text[:50]}...'"
        )
        
        # Логирование деталей результата
        if 'data' in result:
            data = result['data']
            if isinstance(data, dict):
                personal_tasks = data.get('personal_tasks_created', [])
                work_tasks = data.get('work_tasks_created', [])
                if personal_tasks or work_tasks:
                    logger.info(
                        f"Создано задач через AI: личных={len(personal_tasks)}, "
                        f"рабочих={len(work_tasks)}"
                    )
        
        # Форматировать ответ для Telegram
        response_text = coordinator.format_response_for_telegram(result)
        
        # Отправить ответ
        await processing_msg.edit_text(response_text)
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(
            f"Ошибка при обработке AI запроса (время: {elapsed_time:.2f}s): {e}",
            exc_info=True
        )
        error_msg = f"❌ Произошла ошибка при обработке запроса: {str(e)}"
        
        # Попытка обновить сообщение обработки, если оно существует
        try:
            if 'processing_msg' in locals():
                await processing_msg.edit_text(error_msg)
            else:
                await update.message.reply_text(error_msg)
        except:
            await update.message.reply_text(error_msg)

