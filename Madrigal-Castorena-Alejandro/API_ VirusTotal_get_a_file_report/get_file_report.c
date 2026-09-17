#include <stdio.h>
#include <curl/curl.h>

int main(void)
{
    CURL *hnd = curl_easy_init();

    if (hnd == NULL) {
        fprintf(stderr, "No se pudo inicializar CURL\n");
        return 1;
    }

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "accept: application/json");
    // Se incluye la cabecera x-apikey requerida por la API de VirusTotal
    headers = curl_slist_append(headers, "x-apikey: 874e92fd80480fdbc3c036b598ec66241229e18ffbec66a80f65f19eb6ee0e60");

    curl_easy_setopt(hnd, CURLOPT_URL,
        "https://www.virustotal.com/api/v3/files/992b3e05d5eb40e8e9a751b134a7b72a");

    curl_easy_setopt(hnd, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(hnd, CURLOPT_WRITEFUNCTION, NULL);
    curl_easy_setopt(hnd, CURLOPT_WRITEDATA, stdout);

    CURLcode ret = curl_easy_perform(hnd);

    if (ret != CURLE_OK) {
        fprintf(stderr, "Error de CURL: %s\n", curl_easy_strerror(ret));
    }

    curl_slist_free_all(headers);
    curl_easy_cleanup(hnd);

    return ret == CURLE_OK ? 0 : 1;
}
