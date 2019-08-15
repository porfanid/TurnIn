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

import com.jcraft.jsch.JSch;
import com.jcraft.jsch.JSchException;
import com.jcraft.jsch.Session;
import java.io.PrintStream;
import java.util.Scanner;

/**
 *
 * @author porfanid
 */
public class Server implements Comparable<Server>{
    
    public final String host;
    
    public final boolean up;
    
    public final boolean canConnect;
    
    public final int users;
    
    public int portForwarding;
    
    public Server(String hostname,String up,String Users)
    {
        portForwarding=-1;
        host=hostname;
        this.up=up.equals("up");
        canConnect=hostname.startsWith("opti7020ws")||hostname.startsWith("hp6000ws");
        
        users=getInt(Users);
    }
    
    public int getInt(String s)
    {
        try{
            return Integer.parseInt(s);
        }catch(NumberFormatException e)
        {
            return -1;
        }
    }
    
    public String toString()
    {
        return host+ " " +up+ " " +canConnect;
    }
    
    public String ssh()
    {
        return "ssh -t "+host +" ls -la";
    }
    
    public Session[] connect(UserInterface user,Server proxy)
    {
        PrintStream out=user.getOutputStream();
        
        Scanner keyboard=new Scanner(user.getInputStream());
        
        while(true)
        {
            try {
                portForwarding=2234;
                String[] creds=user.creds();
                String username=creds[0];
                String password=creds[1];
                
                Session[] session;
                
                if(proxy==null)
                {
                    session=getSession(username,password,host,null,22,portForwarding);
                }else
                {
                    session=getSession(username,password,host,proxy.host,22,portForwarding);
                }
                
                return session;
            } catch (JSchException ex) {
                String response=ex.getMessage();
                if(response.toLowerCase().contains("auth"))
                {
                    out.println("Wrong credentials. Please try again.");
                    user.refreshCredentials();
                    continue;
                }
                
                if(response.toLowerCase().contains("time"))
                {
                    out.println("Time out error. Try again later");
                    continue;
                }
                
                if(response.toLowerCase().contains("unknownhost"))
                {
                    out.println("The host was not found. Something went wrong.");
                }
                
                out.println("Unknown error.");
                
                ex.printStackTrace(out);
            }
        }
    }
    
    
    
    
    private Session[] getSession(String username,String password,String host,String proxy,int port,int secondaryPort) throws JSchException
    {
        
        if(proxy==null)
        {
            JSch jsch = new JSch();
            
            Session localSession = jsch.getSession(username, host, port);
            localSession.setPassword(password);
            localSession.setConfig("StrictHostKeyChecking", "no");
            localSession.connect();
            return new Session[]{localSession};
        }else
        {
            JSch jsch=new JSch();
            Session session=jsch.getSession(username, proxy, port);
            session.setPassword(password);
            session.setConfig("StrictHostKeyChecking", "no");
            session.setPortForwardingL(portForwarding, host, 22);
            session.connect();
            session.openChannel("direct-tcpip");

            // create a session connected to port 2233 on the local host.
            Session secondSession = jsch.getSession(username, "localhost", portForwarding);
            secondSession.setPassword(password);
            secondSession.setConfig("StrictHostKeyChecking", "no");
            secondSession.connect();
            return new Session[]{session,secondSession};
        }
            
            
    }
    
    
    
    

    @Override
    public int compareTo(Server o) {
        Integer i=users;
        return i.compareTo(o.users);
    }


}
