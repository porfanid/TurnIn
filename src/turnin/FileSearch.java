/* 
 * The MIT License
 *
 * Copyright 2019 porfanid.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */
package turnin;

/**
 *
 * @author porfanid
 */
import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;

public class FileSearch {

    public static ArrayList<File> run(File dir,String fileName)
    {
        ArrayList<File> temp=new ArrayList<File>();
        run(temp,dir,fileName);
        return temp;
    }
    
    
  public static void run(ArrayList<File> list,File dir, String fileName)
  {
      
      File[] listFile=dir.listFiles();
      
        if(listFile==null)
        {
            return;
        }
      
      runOnce(list,dir,fileName);
      
      for(File i:listFile)
      {
          //System.out.println(i);
          if(i.isDirectory())
          {
              run(list,i,fileName);
          }
      }
  }
  
  public static void runOnce(ArrayList<File> list,File dir, String fileName)
  {
        File root = dir;
        //String fileName = "a.txt";
            boolean recursive = true;

            File[] tempList=root.listFiles();
            
            if(tempList==null)
            {
                return;
            }
            
            List<File> files = Arrays.asList(tempList);

            for (Iterator iterator = files.iterator(); iterator.hasNext();) {
                File file = (File) iterator.next();
                if (file.getName().equals(fileName))
                    list.add(file);
            }
  }

}
