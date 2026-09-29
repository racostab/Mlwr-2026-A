import asyncio
from pathlib import Path

from playwright.async_api import async_playwright


# Configuración del repositorio interno del laboratorio
LAB_URL = "https://virusshare.com"
LAB_USER = "xxxxx"
LAB_PASSWORD = "xxxxx"
SAMPLE_ID = "f5ac7c2fd94b1e39aa754f41a31796523ec7c5dee7be5b526ceef2e04d6d135e"

OUTPUT_DIR = Path("./muestras_autorizadas")


async def descargar_muestra_autorizada() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        try:
            await page.goto(f"{LAB_URL}/login", wait_until="domcontentloaded")

            await page.locator('input[name="username"]').fill(LAB_USER)
            await page.locator('input[name="password"]').fill(LAB_PASSWORD)

            await page.locator('input[type="submit"][value="Login"]').click()


            await page.wait_for_load_state("domcontentloaded")

            await page.goto(
                f"{LAB_URL}/file?{SAMPLE_ID}",
                wait_until="domcontentloaded",
            )

            async with page.expect_download() as download_info:
                await page.locator('a[title="Download file"]').click()

            descarga = await download_info.value

            destino = OUTPUT_DIR / descarga.suggested_filename
            await descarga.save_as(destino)

            print(f"Archivo guardado en: {destino}")
                    
        finally:
            await context.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(descargar_muestra_autorizada())
