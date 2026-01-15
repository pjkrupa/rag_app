import markdown
from pathlib import Path
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from rag_app.app.core.config import Configurations
from rag_app.app.core.errors import ConfigurationsError
from rag_app.app.core.logging_setup import get_logger
from rag_app.api.deps import get_session_manager
from rag_app.api.routes import router


def create_app():
    BASE_DIR = Path(__file__).resolve().parent

    templates = Jinja2Templates(directory=BASE_DIR / "templates")
    templates.env.filters["markdown"] = lambda text: markdown.markdown(
        text,
        extensions=["fenced_code", "tables"]
    )

    # sets up the SessionManager object to be loaded into FastAPI as a dependency 
    get_session_manager()

    logger = get_logger()

    # instantiates the configurations by fetching them from a YAML file
    # and logging any problems
    try:
        configs = Configurations.load(logger=logger)
    except ConfigurationsError as e:
        logger.error(f"The configurations didn't load correctly: {e}")


    app = FastAPI(root_path=configs.root_path)
    app.mount(
            "/static",
            StaticFiles(directory=BASE_DIR / "static"),
            name="static",
        )
    
    app.include_router(router)
    app.state.templates = templates
    app.state.configs = configs

    return app

