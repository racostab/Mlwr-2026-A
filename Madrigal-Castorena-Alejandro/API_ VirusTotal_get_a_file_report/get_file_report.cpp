#include <iostream>
#include <curl/curl.h>

int main() {
    CURL *hnd = curl_easy_init();
    if (!hnd) {
        std::cerr << "Error al inicializar cURL" << std::endl;
        return 1;
    }

    // URL sin los %20 en el hash
    curl_easy_setopt(hnd, CURLOPT_URL, "https://www.virustotal.com/api/v3/files/992b3e05d5eb40e8e9a751b134a7b72a");
    curl_easy_setopt(hnd, CURLOPT_HTTPGET, 1L);
    curl_easy_setopt(hnd, CURLOPT_WRITEDATA, stdout);

    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "accept: application/json");
    headers = curl_slist_append(headers, "x-apikey: 874e92fd80480fdbc3c036b598ec66241229e18ffbec66a80f65f19eb6ee0e60");
    curl_easy_setopt(hnd, CURLOPT_HTTPHEADER, headers);

    CURLcode ret = curl_easy_perform(hnd);

    if (ret != CURLE_OK) {
        std::cerr << "Error en la petición: " << curl_easy_strerror(ret) << std::endl;
    }

    // Limpieza de memoria (importante en C++)
    curl_slist_free_all(headers);
    curl_easy_cleanup(hnd);

    return 0;
}
