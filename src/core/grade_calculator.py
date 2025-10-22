"""
Calculadora de notas según la escala chilena
"""

class GradeCalculator:
    """
    Calcula notas según el sistema de evaluación chileno (escala 1.0 - 7.0)
    """
    
    def __init__(self, max_score, passing_percentage, min_grade=1.0, 
                 max_grade=7.0, passing_grade=4.0):
        """
        Inicializa el calculador de notas
        
        Args:
            max_score: Puntaje máximo de la prueba
            passing_percentage: Porcentaje de exigencia (0-100)
            min_grade: Nota mínima (default: 1.0)
            max_grade: Nota máxima (default: 7.0)
            passing_grade: Nota de aprobación (default: 4.0)
        """
        self.max_score = max_score
        self.passing_percentage = passing_percentage
        self.min_grade = min_grade
        self.max_grade = max_grade
        self.passing_grade = passing_grade
        
        # Calcular puntaje mínimo de aprobación
        self.min_passing_score = (max_score * passing_percentage) / 100.0
    
    def calculate_grade(self, obtained_score):
        """
        Calcula la nota según el puntaje obtenido
        
        Args:
            obtained_score: Puntaje obtenido por el estudiante
        
        Returns:
            float: Nota calculada (redondeada a 1 decimal)
        """
        # Si el puntaje es 0, retornar nota mínima
        if obtained_score == 0:
            return self.min_grade
        
        # Si el puntaje es igual o mayor al máximo, retornar nota máxima
        if obtained_score >= self.max_score:
            return self.max_grade
        
        # Si el puntaje es menor al mínimo de aprobación
        if obtained_score < self.min_passing_score:
            # Calcular nota entre nota mínima y nota de aprobación
            grade = self.min_grade + ((obtained_score / self.min_passing_score) * 
                                     (self.passing_grade - self.min_grade))
        else:
            # Calcular nota entre nota de aprobación y nota máxima
            grade = self.passing_grade + (
                (obtained_score - self.min_passing_score) / 
                (self.max_score - self.min_passing_score) * 
                (self.max_grade - self.passing_grade)
            )
        
        # Redondear a 1 decimal
        return round(grade, 1)
    
    def get_grade_info(self, obtained_score):
        """
        Obtiene información detallada de la calificación
        
        Args:
            obtained_score: Puntaje obtenido
        
        Returns:
            dict: Diccionario con información de la nota
        """
        grade = self.calculate_grade(obtained_score)
        
        return {
            'obtained_score': obtained_score,
            'max_score': self.max_score,
            'min_passing_score': round(self.min_passing_score, 1),
            'grade': grade,
            'passed': grade >= self.passing_grade,
            'percentage': round((obtained_score / self.max_score) * 100, 1)
        }
    
    def get_score_for_grade(self, target_grade):
        """
        Calcula el puntaje necesario para obtener una nota específica
        
        Args:
            target_grade: Nota objetivo
        
        Returns:
            float: Puntaje necesario (redondeado a 1 decimal)
        """
        if target_grade <= self.min_grade:
            return 0.0
        
        if target_grade >= self.max_grade:
            return float(self.max_score)
        
        if target_grade < self.passing_grade:
            # Puntaje entre 0 y puntaje mínimo de aprobación
            score = (target_grade - self.min_grade) / \
                   (self.passing_grade - self.min_grade) * self.min_passing_score
        else:
            # Puntaje entre puntaje mínimo de aprobación y puntaje máximo
            score = self.min_passing_score + \
                   ((target_grade - self.passing_grade) / 
                    (self.max_grade - self.passing_grade) * 
                    (self.max_score - self.min_passing_score))
        
        return round(score, 1)