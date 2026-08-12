import logging

def get_logger(name: str) -> logging.Logger:
    """
    Scopo: Fornisce un'istanza di logger configurata standard per il modulo specificato.

    Parametri:
    - name (str): Il nome del modulo (solitamente __name__).

    Valore di ritorno:
    - logging.Logger: Istanza configurata del logger.

    Eccezioni:
    - Nessuna eccezione prevista.
    """
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger
