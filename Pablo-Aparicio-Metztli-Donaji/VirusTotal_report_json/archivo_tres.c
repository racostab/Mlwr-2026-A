CURL *hnd = curl_easy_init();

curl_easy_setopt(hnd, CURLOPT_CUSTOMREQUEST, "GET");
curl_easy_setopt(hnd, CURLOPT_WRITEDATA, stdout);
curl_easy_setopt(hnd, CURLOPT_URL, "https://www.virustotal.com/api/v3/files/1dc34e167c6d1b66172f90288b241bc7");

struct curl_slist *headers = NULL;
headers = curl_slist_append(headers, "accept: application/json");
headers = curl_slist_append(headers, "x-apikey: 899adc0d8237c25d9500293250c4b9fd15a269ac393c8ac16d8bfd10ac9fa932");
curl_easy_setopt(hnd, CURLOPT_HTTPHEADER, headers);

CURLcode ret = curl_easy_perform(hnd);
