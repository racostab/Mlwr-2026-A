#include <iostream>
#include <string>
#include <curl/curl.h>

// Callback para acumular la respuesta en un std::string
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    size_t totalSize = size * nmemb;
    userp->append((char*)contents, totalSize);
    return totalSize;
}

int main() {
    CURL* curl;
    CURLcode res;
    std::string readBuffer;
    struct curl_slist* headers = NULL;

    curl_global_init(CURL_GLOBAL_DEFAULT);
    curl = curl_easy_init();

    if(curl) {
        curl_easy_setopt(curl, CURLOPT_URL, "https://www.virustotal.com/api/v3/files/%2033c39c78b9aa5ce8ad78dfd41df81792%20");
        
        // Configurar los encabezados (Headers)
        headers = curl_slist_append(headers, "accept: application/json");
        headers = curl_slist_append(headers, "x-apikey: a59be554b4190f7228f679d9c7f23f4f9c8c52a3134ebcb732dfe21521e1506e");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        
        // Configurar callback y el buffer de destino
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &readBuffer);

        // Ejecutar la petición
        res = curl_easy_perform(curl);
        
        if(res != CURLE_OK) {
            std::cerr << "curl_easy_perform() falló: " << curl_easy_strerror(res) << std::endl;
        } else {
            // Imprimir el texto de la respuesta (equivalente a response.text)
            std::cout << readBuffer << std::endl;
        }

        // Liberar memoria
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
    }
    
    curl_global_cleanup();
    return 0;
}