#include <stdio.h>
#include <stdlib.h>
#include <curl/curl.h>

// Callback para escribir/imprimir la respuesta
size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t total_size = size * nmemb;
    printf("%.*s", (int)total_size, (char *)contents);
    return total_size;
}

int main(void) {
    CURL *curl;
    CURLcode res;
    struct curl_slist *headers = NULL;

    // Inicialización global de libcurl
    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if(curl) {
        // URL de la API
        curl_easy_setopt(curl, CURLOPT_URL, "https://www.virustotal.com/api/v3/files/%2033c39c78b9aa5ce8ad78dfd41df81792%20");
        
        // Configurar los encabezados (Headers)
        headers = curl_slist_append(headers, "accept: application/json");
        headers = curl_slist_append(headers, "x-apikey: a59be554b4190f7228f679d9c7f23f4f9c8c52a3134ebcb732dfe21521e1506e");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        
        // Configurar la función callback para recibir los datos
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);

        // Ejecutar la petición
        res = curl_easy_perform(curl);
        
        // Comprobar errores
        if(res != CURLE_OK) {
            fprintf(stderr, "\ncurl_easy_perform() falló: %s\n", curl_easy_strerror(res));
        } else {
            printf("\n"); // Salto de línea al final para mejor legibilidad
        }

        // Liberar memoria
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
    
    // Limpieza global
    curl_global_cleanup();
    return 0;
}