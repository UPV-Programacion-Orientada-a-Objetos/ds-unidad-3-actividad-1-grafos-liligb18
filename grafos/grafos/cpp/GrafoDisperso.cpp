#include "GrafoDisperso.h"
#include <fstream>
#include <sstream>
#include <queue>
#include <set>
#include <algorithm>
#include <chrono>

GrafoDisperso::GrafoDisperso() 
    : num_nodos(0), num_aristas(0), siguiente_indice(0) {
    std::cout << "[C++ Core] Inicializando GrafoDisperso..." << std::endl;
}

GrafoDisperso::~GrafoDisperso() {
    std::cout << "[C++ Core] Destruyendo GrafoDisperso..." << std::endl;
}

int GrafoDisperso::obtenerIndice(int id) {
    if (id_to_index.find(id) == id_to_index.end()) {
        id_to_index[id] = siguiente_indice;
        index_to_id[siguiente_indice] = id;
        siguiente_indice++;
    }
    return id_to_index[id];
}

int GrafoDisperso::obtenerId(int indice) {
    if (index_to_id.find(indice) != index_to_id.end()) {
        return index_to_id[indice];
    }
    return -1;
}

void GrafoDisperso::cargarDatos(const std::string& nombreArchivo) {
    std::cout << "[C++ Core] Cargando dataset '" << nombreArchivo << "'..." << std::endl;
    
    auto inicio = std::chrono::high_resolution_clock::now();
    
    // Estructura temporal para almacenar aristas por nodo origen
    std::map<int, std::vector<int>> lista_adyacencia_temp;
    
    std::ifstream archivo(nombreArchivo);
    if (!archivo.is_open()) {
        std::cerr << "[C++ Core] ERROR: No se pudo abrir el archivo." << std::endl;
        return;
    }
    
    std::string linea;
    int aristas_leidas = 0;
    
    // Leer archivo línea por línea
    while (std::getline(archivo, linea)) {
        // Saltar comentarios y líneas vacías
        if (linea.empty() || linea[0] == '#') {
            continue;
        }
        
        std::istringstream iss(linea);
        int origen, destino;
        
        if (iss >> origen >> destino) {
            // Convertir IDs a índices internos
            int idx_origen = obtenerIndice(origen);
            int idx_destino = obtenerIndice(destino);
            
            lista_adyacencia_temp[idx_origen].push_back(idx_destino);
            aristas_leidas++;
        }
    }
    
    archivo.close();
    
    num_nodos = siguiente_indice;
    num_aristas = aristas_leidas;
    
    // Construir estructura CSR
    row_ptr.resize(num_nodos + 1, 0);
    
    // Calcular row_ptr (punteros de inicio de cada fila)
    for (int i = 0; i < num_nodos; i++) {
        if (lista_adyacencia_temp.find(i) != lista_adyacencia_temp.end()) {
            row_ptr[i + 1] = row_ptr[i] + lista_adyacencia_temp[i].size();
        } else {
            row_ptr[i + 1] = row_ptr[i];
        }
    }
    
    // Construir col_indices (índices de columnas/destinos)
    col_indices.resize(num_aristas);
    int pos = 0;
    for (int i = 0; i < num_nodos; i++) {
        if (lista_adyacencia_temp.find(i) != lista_adyacencia_temp.end()) {
            for (int vecino : lista_adyacencia_temp[i]) {
                col_indices[pos++] = vecino;
            }
        }
    }
    
    auto fin = std::chrono::high_resolution_clock::now();
    auto duracion = std::chrono::duration_cast<std::chrono::milliseconds>(fin - inicio);
    
    std::cout << "[C++ Core] Carga completa. Nodos: " << num_nodos 
              << " | Aristas: " << num_aristas << std::endl;
    std::cout << "[C++ Core] Tiempo de carga: " << duracion.count() << " ms" << std::endl;
    std::cout << "[C++ Core] Estructura CSR construida. Memoria estimada: " 
              << obtenerMemoriaEstimada() / (1024 * 1024) << " MB." << std::endl;
}

std::vector<int> GrafoDisperso::BFS(int nodoInicio, int profundidadMaxima) {
    std::cout << "[Cython] Solicitud recibida: BFS desde Nodo " << nodoInicio 
              << ", Profundidad " << profundidadMaxima << "." << std::endl;
    
    auto inicio = std::chrono::high_resolution_clock::now();
    
    std::vector<int> nodos_visitados;
    
    // Convertir ID a índice interno
    int idx_inicio = obtenerIndice(nodoInicio);
    
    if (idx_inicio >= num_nodos || idx_inicio < 0) {
        std::cerr << "[C++ Core] ERROR: Nodo de inicio inválido." << std::endl;
        return nodos_visitados;
    }
    
    std::queue<std::pair<int, int>> cola; // (índice_nodo, profundidad)
    std::set<int> visitados;
    
    cola.push({idx_inicio, 0});
    visitados.insert(idx_inicio);
    
    while (!cola.empty()) {
        auto [nodo_actual, profundidad] = cola.front();
        cola.pop();
        
        // Agregar nodo visitado (convertir índice a ID original)
        nodos_visitados.push_back(obtenerId(nodo_actual));
        
        if (profundidad >= profundidadMaxima) {
            continue;
        }
        
        // Obtener vecinos usando CSR
        int inicio_vecinos = row_ptr[nodo_actual];
        int fin_vecinos = row_ptr[nodo_actual + 1];
        
        for (int i = inicio_vecinos; i < fin_vecinos; i++) {
            int vecino = col_indices[i];
            
            if (visitados.find(vecino) == visitados.end()) {
                visitados.insert(vecino);
                cola.push({vecino, profundidad + 1});
            }
        }
    }
    
    auto fin = std::chrono::high_resolution_clock::now();
    auto duracion = std::chrono::duration_cast<std::chrono::microseconds>(fin - inicio);
    
    std::cout << "[C++ Core] Ejecutando BFS nativo..." << std::endl;
    std::cout << "[C++ Core] Nodos encontrados: " << nodos_visitados.size() 
              << ". Tiempo ejecución: " << duracion.count() / 1000.0 << " ms." << std::endl;
    
    return nodos_visitados;
}

int GrafoDisperso::obtenerGrado(int nodo) {
    int idx = obtenerIndice(nodo);
    
    if (idx >= num_nodos || idx < 0) {
        return -1;
    }
    
    // El grado de salida se obtiene directamente del CSR
    return row_ptr[idx + 1] - row_ptr[idx];
}

std::vector<int> GrafoDisperso::getVecinos(int nodo) {
    std::vector<int> vecinos;
    int idx = obtenerIndice(nodo);
    
    if (idx >= num_nodos || idx < 0) {
        return vecinos;
    }
    
    int inicio = row_ptr[idx];
    int fin = row_ptr[idx + 1];
    
    for (int i = inicio; i < fin; i++) {
        vecinos.push_back(obtenerId(col_indices[i]));
    }
    
    return vecinos;
}

int GrafoDisperso::obtenerNumNodos() const {
    return num_nodos;
}

int GrafoDisperso::obtenerNumAristas() const {
    return num_aristas;
}

std::pair<int, int> GrafoDisperso::obtenerNodoMaxGrado() {
    int max_grado = -1;
    int nodo_max = -1;
    
    for (int i = 0; i < num_nodos; i++) {
        int grado = row_ptr[i + 1] - row_ptr[i];
        if (grado > max_grado) {
            max_grado = grado;
            nodo_max = i;
        }
    }
    
    return {obtenerId(nodo_max), max_grado};
}

std::vector<std::pair<int, int>> GrafoDisperso::obtenerAristasSubgrafo(const std::vector<int>& nodos) {
    std::vector<std::pair<int, int>> aristas;
    std::set<int> conjunto_nodos;
    
    // Convertir a conjunto para búsqueda rápida
    for (int nodo : nodos) {
        conjunto_nodos.insert(nodo);
    }
    
    // Para cada nodo en el subgrafo
    for (int nodo : nodos) {
        int idx = obtenerIndice(nodo);
        
        if (idx >= num_nodos || idx < 0) {
            continue;
        }
        
        // Obtener vecinos
        int inicio = row_ptr[idx];
        int fin = row_ptr[idx + 1];
        
        for (int i = inicio; i < fin; i++) {
            int id_vecino = obtenerId(col_indices[i]);
            
            // Solo incluir aristas donde ambos nodos estén en el subgrafo
            if (conjunto_nodos.find(id_vecino) != conjunto_nodos.end()) {
                aristas.push_back({nodo, id_vecino});
            }
        }
    }
    
    std::cout << "[Cython] Retornando lista de adyacencia local a Python." << std::endl;
    return aristas;
}

void GrafoDisperso::imprimirEstadisticas() const {
    std::cout << "=== Estadísticas del Grafo ===" << std::endl;
    std::cout << "Nodos: " << num_nodos << std::endl;
    std::cout << "Aristas: " << num_aristas << std::endl;
    std::cout << "Memoria estimada: " << obtenerMemoriaEstimada() / (1024 * 1024) << " MB" << std::endl;
}

size_t GrafoDisperso::obtenerMemoriaEstimada() const {
    size_t memoria = 0;
    
    // Vectores CSR
    memoria += row_ptr.size() * sizeof(int);
    memoria += col_indices.size() * sizeof(int);
    
    // Mapas
    memoria += id_to_index.size() * (sizeof(int) * 2 + 32); // Estimación para std::map
    memoria += index_to_id.size() * (sizeof(int) * 2 + 32);
    
    return memoria;
}
